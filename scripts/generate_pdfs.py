#builds the four recipe book pdfs (a4 and booklet, metric and freedom units) from recipes/*.md with weasyprint
#run from the repo root
#requires pandoc, and python packages weasyprint and fonttools
import re, html, datetime, subprocess, unicodedata
from pathlib import Path
import pydyf
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from units import to_freedom
from common import humanize, years, recipe_tags, tag_groups

version = Path('version.txt').read_text().strip()
font_file = Path('assets/fonts/nunito-extrabold.ttf')
now = datetime.datetime.now()
#first tag found picks the section, in book order
sections = {'snack': 'snacks', 'breakfast': 'breakfast', 'lunch': 'lunch', 'dinner': 'dinner',
            'dessert': 'dessert', 'sides': 'sides', None: 'extra stuff'}

#tags in the hidden group (tags/groups.txt) stay off the book
hidden_tags = tag_groups()[1]

def md_to_html(text, prefix=''):
    return subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html5', '--id-prefix=' + prefix],
                          input=text, capture_output=True, text=True, encoding='utf-8', check=True).stdout

def build_fractions(text):
    #the font lacks most fraction glyphs and falls back to a lighter one, so build them from small digits
    def build(match):
        top, bottom = (''.join(chr(int(c, 16)) for c in side.split())
                       for side in unicodedata.decomposition(match.group())[11:].split(' 2044 '))
        return '<span class="num">' + top + '</span>⁄<span class="den">' + bottom + '</span>'
    return re.sub('[⅐-⅞↉]', build, text)

def recipe_html(slug, tags, section, edition):
    text = Path('recipes', slug + '.md').read_text(encoding='utf-8')
    #the site's footer extras: logo, badges and view counter
    text = '\n'.join(l for l in text.split('\n') if not re.search(r'logo_sm\.png|count\.svg|img\.shields\.io', l))
    if edition == 'freedom':
        text = ''.join(to_freedom(l) for l in text.splitlines(True))
    text = build_fractions(text)
    serves = re.search(r'^\*\*Serves:\*\*[ \t]*(.+)$', text, re.M)
    text = re.sub(r'^\*\*Serves:\*\*.*\n?', '', text, flags=re.M)
    #the main photo becomes a banner above the title
    hero = re.search(r'^<img[^>]*src="([^"]*/images/main\.\w+)"[^>]*>[ \t]*\n?', text, re.M)
    if hero:
        text = text[:hero.start()] + text[hero.end():]
    #ingredients in a panel beside the method, which wraps under it when longer
    text = re.sub(r'^(## Ingredients[ \t]*\n(?:(?!## ).*\n)*)(## Method[ \t]*\n(?:(?!## |<p class="recipe-dates").*\n)*)',
                  lambda m: '<div class="ingredients">\n\n' + m[1] + '\n</div>\n<div class="method">\n\n' + m[2] + '\n</div>\n\n',
                  text.rstrip('\n') + '\n', flags=re.M)
    #tips in one box that moves to the next page whole
    text = re.sub(r'^(## Tips[ \t]*\n.*?)(?=^## |^<p class="recipe-dates"|\Z)',
                  lambda m: '<div class="tips">\n\n' + m[1].rstrip() + '\n\n</div>\n\n', text, flags=re.M | re.S)
    chips = ['<span class="fact">Serves ' + html.escape(serves[1].strip()) + '</span>'] if serves else []
    chips += ['<span class="tag">' + html.escape(t.replace('_', ' ')) + '</span>' for t in tags if t not in hidden_tags]
    top = (('<img class="hero" src="' + html.escape(hero[1]) + '">' if hero else '') +
           '<p class="kicker">' + section + '</p>')
    body = md_to_html(text, slug + '-').replace('<h1', top + '<h1', 1)
    body = re.sub(r'(</h1>)', r'\1<p class="facts">' + ' '.join(chips) + '</p>', body, count=1)
    return '<article id="' + slug + '">' + body + '</article>'

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
    for md in sorted(Path('recipes').glob('*.md')):
        tags = recipe_tags(md.parent / md.stem)
        section = sections[next((t for t in sections if t in tags), None)]
        recipe_title = re.search(r'^# (.+)$', md.read_text(encoding='utf-8'), re.M)[1].strip()
        book[section].append((md.stem, recipe_title, recipe_html(md.stem, tags, section, edition)))
    contents = ''.join('<h2>%s</h2>' % name + ''.join('<a href="#%s">%s</a>' % (slug, html.escape(t)) for slug, t, _ in rs)
                       for name, rs in book.items() if rs)
    recipes = ''.join(divider_html(name, [t for _, t, _ in rs]) + ''.join(r for _, _, r in rs) for name, rs in book.items() if rs)

    for layout in ('a4', 'booklet'):
        #a4 is one page per sheet, the booklet has larger text for printing two pages per side
        label = ('A4' if layout == 'a4' else 'Booklet') + ' edition · ' + ('metric' if edition == 'metric' else 'freedom units')
        title = 'gitFOOD Recipe Book (%s)' % label
        filename = 'gitFOOD_Recipe_Book' + ('-booklet' if layout == 'booklet' else '') + ('-freedom' if edition == 'freedom' else '') + '.pdf'
        title_page = Path('pdf/title_page.md').read_text(encoding='utf-8').format(
            version_number=version, edition=label, years=years(now.year), date=humanize(now.date().isoformat()))
        print('rendering ' + filename)
        page = ('<!doctype html><html lang="en" class="%s"><head><meta charset="utf-8"><title>%s</title>'
                '<meta name="author" content="fexofenadine"><meta name="keywords" content="gitFOOD, recipes, cookbook, %s, version %s">'
                '<meta name="description" content="%s %s, recipes from https://foodgit.github.io/">'
                '<meta name="generator" content="gitFOOD generate_pdfs.py (weasyprint)"><meta name="dcterms.created" content="%s">'
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
