#builds the recipe books from recipes/*/*.recipe: four pdfs (a4 and booklet, metric and freedom units) and two epubs
#run from the repo root, needs python packages weasyprint, fonttools and markdown-it-py
import io, re, html, datetime, unicodedata, zipfile
from functools import cache
from pathlib import Path
import pydyf
from PIL import Image, ImageOps
from markdown_it import MarkdownIt
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from units import to_freedom
from common import git_dates, humanize, years, recipe_tags, tag_groups

version = Path('version.txt').read_text().strip()
font_file = Path('assets/fonts/nunito-extrabold.ttf')
now = datetime.datetime.now()
#first tag found picks the section, in book order
sections = {'snack': 'snacks', 'breakfast': 'breakfast', 'lunch': 'lunch', 'dinner': 'dinner',
            'dessert': 'dessert', 'sides': 'sides', None: 'extra stuff'}

#tags in the hidden group (tags/groups.txt) stay off the book
hidden_tags = tag_groups()[1]
md_to_html = MarkdownIt('commonmark', {'html': True}).enable('table').render
md_to_xhtml = MarkdownIt('commonmark', {'html': True, 'xhtmlOut': True}).enable('table').render

def build_fractions(text):
    #the font lacks most fraction glyphs and falls back to a lighter one, so build them from small digits
    def build(match):
        top, bottom = (''.join(chr(int(c, 16)) for c in side.split())
                       for side in unicodedata.decomposition(match.group())[11:].split(' 2044 '))
        return '<span class="num">' + top + '</span>⁄<span class="den">' + bottom + '</span>'
    return re.sub('[⅐-⅞↉]', build, text)

def photo_rows(method):
    #a step's photos go in a row under its text, each half the width, so a single photo matches a pair
    def row(imgs):
        return '<div class="photos">' + ''.join(imgs) + '</div>'
    def step(m):
        imgs = re.findall(r'<img [^>]*>', m[3])
        if not imgs:
            return m[0]
        text = re.sub(r'\s*<img [^>]*>', '', m[3])
        return m[1] + text + (row(imgs) + m[4] if m[2] == 'li' else m[4] + row(imgs))
    method = re.sub(r'(<(li|h[2-6])>)(.*?)(</\2>)', step, method, flags=re.S)
    #photos between steps, on lines of their own
    return re.sub(r'(?m)^<img [^>]*>(?:\s*<img [^>]*>)*', lambda m: row(re.findall(r'<img [^>]*>', m[0])), method)

def recipe_markdown(stub, edition, image):
    #the recipe in the edition's units with its serves line taken out, photos made by image(name), and its dates
    text = stub.read_text(encoding='utf-8')
    if edition == 'freedom':
        text = ''.join(to_freedom(l) for l in text.splitlines(True))
    serves = re.search(r'^\*\*Serves:\*\*[ \t]*(.+)$', text, re.M)
    text = re.sub(r'^\*\*Serves:\*\*.*\n?', '', text, flags=re.M)
    #{photo.jpg} placeholders become images, the main photo goes above the title
    photos = {p.name for p in (stub.parent / 'images').glob('*.jpg')}
    hero = '{main.jpg}' in text and 'main.jpg' in photos
    text = re.sub(r'\{([^{}\s]+\.jpg)\}', lambda m: '' if m[1] == 'main.jpg' else image(m[1]) if m[1] in photos else m[0], text)
    updated, created = git_dates(stub)
    return text, serves[1].strip() if serves else '', hero, 'Created: %s · Last updated: %s' % (humanize(created), humanize(updated))

def recipe_html(stub, tags, section, edition):
    slug = stub.stem
    text, serves, hero, dates = recipe_markdown(stub, edition, lambda name: '<img src="%s/images/%s" align="right">' % (slug, name))
    text = build_fractions(text)
    hero = '<img class="hero" src="%s/images/main.jpg">' % slug if hero else ''
    #ingredients in a panel beside the method, which wraps under it when longer
    text = re.sub(r'^(## Ingredients[ \t]*\n(?:(?!## ).*\n)*)(## Method[ \t]*\n(?:(?!## ).*\n)*)',
                  lambda m: '<div class="ingredients">\n\n' + m[1] + '\n</div>\n<div class="method">\n\n' + m[2] + '\n</div>\n\n',
                  text.rstrip('\n') + '\n', flags=re.M)
    #tips in one box that moves to the next page whole
    text = re.sub(r'^(## Tips[ \t]*\n.*?)(?=^## |\Z)',
                  lambda m: '<div class="tips">\n\n' + m[1].rstrip() + '\n\n</div>\n\n', text, flags=re.M | re.S)
    chips = ['<span class="fact">Serves ' + build_fractions(html.escape(serves)) + '</span>'] if serves else []
    chips += ['<span class="tag">' + html.escape(t.replace('_', ' ')) + '</span>' for t in tags if t not in hidden_tags]
    body = md_to_html(text).replace('<h1', hero + '<p class="kicker">' + section + '</p><h1', 1)
    body = re.sub(r'(</h1>)', r'\1<p class="facts">' + ' '.join(chips) + '</p>', body, count=1)
    body = re.sub(r'<div class="method">.*?</div>', lambda m: photo_rows(m[0]), body, count=1, flags=re.S)
    #dates go at the end of the last line, so they can never be left alone on a page
    dates = '<span class="recipe-dates">' + dates + '</span>'
    body = re.sub(r'(.*)(</(?:li|p)>)', lambda m: m[1] + dates + m[2], body, count=1, flags=re.S)
    return '<article id="' + slug + '">' + body + '</article>'

def epub_chapter(stub, edition):
    #plain black and white: the photos in greyscale, no panels, chips or footers
    image = lambda name: '<img src="images/%s/%s" alt=""/>' % (stub.stem, name)
    text, serves, hero, dates = recipe_markdown(stub, edition, image)
    body = (image('main.jpg') if hero else '') + md_to_xhtml(text)
    if serves:
        body = body.replace('</h1>', '</h1><p class="serves">Serves ' + html.escape(serves) + '</p>', 1)
    #xhtml knows only the xml entities
    body = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[\da-fA-F]+);)\w+;', lambda m: html.unescape(m[0]), body)
    return body + '<p class="dates">' + dates + '</p>'

@cache
def epub_photo(path):
    #small greyscale jpegs for e-ink screens
    im = ImageOps.exif_transpose(Image.open(path)).convert('L')
    im.thumbnail((800, 800))
    out = io.BytesIO()
    im.save(out, 'JPEG', quality=70, optimize=True)
    return out.getvalue()

EPUB_CSS = """h1 { font-size: 1.5em; margin: .6em 0 .2em; }
h2 { font-size: 1.2em; margin: 1.2em 0 .3em; border-bottom: 1px solid; }
h3 { font-size: 1em; margin: 1em 0 .2em; }
img { display: block; max-width: 100%; margin: .5em auto; }
blockquote { margin: 0; }
li { margin: .3em 0; }
.serves { margin-top: 0; font-style: italic; }
.dates { margin-top: 2em; font-size: .8em; }
nav ol { list-style: none; padding-left: 1em; }
"""

def write_epub(filename, title, label, book):
    #epub 3 with an epub 2 contents too, which some e-readers still use
    def page(heading, body):
        return ('<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
                'lang="en" xml:lang="en"><head><meta charset="utf-8"/><title>%s</title><link rel="stylesheet" href="book.css"/></head><body>%s</body></html>'
                % (html.escape(heading), body))
    files = {'book.css': EPUB_CSS, 'title.xhtml': page(title, (
        '<h1>gitFOOD</h1><p>awesome recipe book</p><p>version %s<br/>%s<br/>https://foodgit.github.io</p><p>Last updated on %s</p>'
        '<p>Copyright © %s fexofenadine. Recipes and photos are licensed under Creative Commons Attribution-ShareAlike 4.0 '
        '(creativecommons.org/licenses/by-sa/4.0).</p>') % (version, label, humanize(now.date().isoformat()), years(now.year)))}
    nav, ncx, n = [], [], 0
    for name, rs in book.items():
        if not rs:
            continue
        n += 1
        points = ''
        for slug, recipe_title, _, chapter in rs:
            files[slug + '.xhtml'] = page(recipe_title, chapter)
            n += 1
            points += '<navPoint id="p%d"><navLabel><text>%s</text></navLabel><content src="%s.xhtml"/></navPoint>' % (n, html.escape(recipe_title), slug)
        nav.append('<li><a href="%s.xhtml">%s</a><ol>%s</ol></li>' % (rs[0][0], name, ''.join(
            '<li><a href="%s.xhtml">%s</a></li>' % (slug, html.escape(t)) for slug, t, _, _ in rs)))
        ncx.append('<navPoint id="s%d"><navLabel><text>%s</text></navLabel><content src="%s.xhtml"/>%s</navPoint>' % (n, name, rs[0][0], points))
    files['nav.xhtml'] = page('Contents', '<nav epub:type="toc"><h1>Contents</h1><ol>%s</ol></nav>' % ''.join(nav))
    uid = 'urn:gitfood:recipe-book:' + label.split(' · ')[-1].replace(' ', '-')
    files['toc.ncx'] = ('<?xml version="1.0" encoding="utf-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
                        '<head><meta name="dtb:uid" content="%s"/></head><docTitle><text>%s</text></docTitle><navMap>%s</navMap></ncx>'
                        % (uid, html.escape(title), ''.join(ncx)))
    photos = sorted({m for f in files.values() for m in re.findall(r'src="(images/[^"]+)"', f)})
    chapters = ['title.xhtml', 'nav.xhtml'] + [slug + '.xhtml' for rs in book.values() for slug, _, _, _ in rs]
    types = {'.css': 'text/css', '.ncx': 'application/x-dtbncx+xml', '.jpg': 'image/jpeg', '.xhtml': 'application/xhtml+xml'}
    manifest = ''.join('<item id="i%d" href="%s" media-type="%s"%s/>' % (i, f, types[Path(f).suffix], ' properties="nav"' if f == 'nav.xhtml' else '')
                       for i, f in enumerate(list(files) + photos))
    ids = {f: 'i%d' % i for i, f in enumerate(list(files) + photos)}
    opf = ('<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="en">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">%s</dc:identifier><dc:title>%s</dc:title>'
           '<dc:language>en</dc:language><dc:creator>fexofenadine</dc:creator><dc:rights>CC BY-SA 4.0</dc:rights>'
           '<meta property="dcterms:modified">%s</meta></metadata><manifest>%s</manifest><spine toc="%s">%s</spine></package>') % (
           uid, html.escape(title), now.strftime('%Y-%m-%dT%H:%M:%SZ'), manifest, ids['toc.ncx'],
           ''.join('<itemref idref="%s"/>' % ids[c] for c in chapters))
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                   '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr('OEBPS/content.opf', opf)
        for f, data in files.items():
            z.writestr('OEBPS/' + f, data)
        for f in photos:
            slug, name = f.split('/')[1:]
            z.writestr('OEBPS/' + f, epub_photo(Path('recipes', slug, 'images', name)))
    print('%s: %d recipes, %d photos' % (filename, len(chapters) - 2, len(photos)))

def outline(text, size):
    #svg path of text in the book font and its width, for the section title on divider pages
    font = TTFont(font_file)
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    scale, pen, x = size / font['head'].unitsPerEm, SVGPathPen(glyphs), 0
    for ch in text:
        if ord(ch) in cmap:
            glyphs[cmap[ord(ch)]].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
            x += glyphs[cmap[ord(ch)]].width * scale
    return pen.getCommands(), x

def divider_html(name, titles):
    #outlined title, recipe count and names, cut short for long sections
    path, width = outline(name, 74)
    shown = titles if len(titles) <= 12 else titles[:12] + ['and %d more' % (len(titles) - 12)]
    return ('<section class="divider" style="bookmark-label: \'%s\'"><div class="band"></div>'
            '<svg width="210mm" height="297mm" viewBox="0 0 595 842"><path transform="translate(%.2f 447)" d="%s" '
            'fill="#00abeb" stroke="#065979" stroke-width="1.1" stroke-linejoin="round"/></svg>'
            '<p class="count">%d recipe%s</p><p class="names">%s</p><div class="band bottom"></div></section>') % (
            name, 297.6 - width / 2, path, len(titles), '' if len(titles) == 1 else 's',
            ' &middot; '.join(html.escape(t) for t in shown))

def viewer_defaults(document, pdf):
    #open with the bookmarks showing and the book title in the title bar
    pdf.catalog['PageMode'] = '/UseOutlines'
    pdf.catalog['ViewerPreferences'] = pydyf.Dictionary({'DisplayDocTitle': 'true'})

fonts = FontConfiguration()
stylesheet = CSS('pdf/book.css', font_config=fonts)
for edition in ('metric', 'freedom'):
    #recipes grouped by section, each sorted by file name
    book = {name: [] for name in sections.values()}
    for stub in sorted(Path('recipes').glob('*/*.recipe')):
        tags = recipe_tags(stub.parent)
        section = sections[next((t for t in sections if t in tags), None)]
        recipe_title = re.search(r'^# (.+)$', stub.read_text(encoding='utf-8'), re.M)[1].strip()
        book[section].append((stub.stem, recipe_title, recipe_html(stub, tags, section, edition), epub_chapter(stub, edition)))
    units = 'metric' if edition == 'metric' else 'freedom units'
    suffix = '' if edition == 'metric' else '-freedom'
    write_epub('gitFOOD_Recipe_Book%s.epub' % suffix, 'gitFOOD Recipe Book (ebook edition · %s)' % units, 'ebook edition · ' + units, book)
    contents = ''.join('<h2>%s</h2>' % name + ''.join('<a href="#%s">%s</a>' % (slug, html.escape(t)) for slug, t, _, _ in rs)
                       for name, rs in book.items() if rs)
    recipes = ''.join(divider_html(name, [t for _, t, _, _ in rs]) + ''.join(r for _, _, r, _ in rs) for name, rs in book.items() if rs)

    for layout in ('a4', 'booklet'):
        #a4 is one page per sheet, the booklet has larger text for printing two pages per side
        label = ('A4' if layout == 'a4' else 'Booklet') + ' edition · ' + units
        title = 'gitFOOD Recipe Book (%s)' % label
        filename = 'gitFOOD_Recipe_Book' + ('-booklet' if layout == 'booklet' else '') + suffix + '.pdf'
        title_page = Path('pdf/title_page.md').read_text(encoding='utf-8').format(
            version_number=version, edition=label, years=years(now.year), date=humanize(now.date().isoformat()))
        print('rendering ' + filename)
        page = ('<!doctype html><html lang="en" class="%s"><head><meta charset="utf-8"><title>%s</title>'
                '<meta name="author" content="fexofenadine"><meta name="keywords" content="gitFOOD, recipes, cookbook, %s, version %s">'
                '<meta name="description" content="%s %s, recipes from https://foodgit.github.io/">'
                '<meta name="generator" content="gitFOOD generate_books.py (weasyprint)"><meta name="dcterms.created" content="%s">'
                '</head><body>') % (layout, title, label, version, title, version, now.date().isoformat())
        page += ('<section class="front"><img src="../images/logo_md.png"><p>welcome to</p></section>'
                 '<section class="blank">&nbsp;</section><section class="title-page">' + md_to_html(title_page) + '</section>'
                 '<section class="contents"><h1>contents</h1>' + contents + '</section>' + recipes +
                 '<section class="back"><p>&copy; gitFOOD %d</p></section></body></html>' % now.year)
        doc = HTML(string=page, base_url='recipes/').render(
            stylesheets=[stylesheet], font_config=fonts, optimize_images=True, jpeg_quality=85, dpi=200)
        #blank pages before the back cover, so it lands on the back of the last sheet
        #booklets fold sheets of four pages
        pad = -len(doc.pages) % (4 if layout == 'booklet' else 2)
        doc = doc.copy(doc.pages[:-1] + [doc.pages[1]] * pad + doc.pages[-1:])
        doc.write_pdf(filename, finisher=viewer_defaults)
        print('%s: %d pages' % (filename, len(doc.pages)))
