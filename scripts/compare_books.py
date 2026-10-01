#compares two recipe book pdfs page by page and exits 0 if the pages are the same, 1 if not
#needs poppler-utils (pdftotext, pdfimages, pdffonts)
import hashlib, re, subprocess, sys

#the cover, blank page and title page come first and the back cover last
#their text (version, date, copyright, year) is not recipe content
SKIP_FIRST = 3
SKIP_LAST = 1

def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout

def page_count(pdf):
    return int(re.search(r'^Pages:\s+(\d+)', run('pdfinfo', pdf), re.M).group(1))

def fingerprint(pdf, page):
    #word positions and text, rounded so tiny renderer differences do not count
    words = re.findall(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)<',
                       run('pdftotext', '-bbox', '-f', str(page), '-l', str(page), pdf, '-'))
    text = [(round(float(a)), round(float(b)), round(float(c)), round(float(d)), w) for a, b, c, d, w in words]
    #image sizes and fonts, without the object ids or subset prefixes that change between builds
    images = [line.split()[3:6] for line in run('pdfimages', '-list', '-f', str(page), '-l', str(page), pdf).splitlines()[2:]]
    fonts = sorted({re.sub(r'^[A-Z]{6}\+', '', line.split()[0]) for line in run('pdffonts', '-f', str(page), '-l', str(page), pdf).splitlines()[2:]})
    return hashlib.sha1(repr((text, images, fonts)).encode()).hexdigest()

def pages(pdf):
    count = page_count(pdf)
    return [fingerprint(pdf, p) for p in range(SKIP_FIRST + 1, count - SKIP_LAST + 1)]

if __name__ == '__main__':
    old, new = pages(sys.argv[1]), pages(sys.argv[2])
    if old == new:
        print(f'pages are the same ({len(new)} compared)')
        sys.exit(0)
    differing = [i + SKIP_FIRST + 1 for i, (a, b) in enumerate(zip(old, new)) if a != b]
    print(f'pages differ: {len(old)} pages before, {len(new)} now, first differing page {differing[0] if differing else "after the shorter book ends"}')
    sys.exit(1)
