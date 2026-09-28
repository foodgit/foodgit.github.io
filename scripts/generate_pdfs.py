# linux only for now 
# requires poppler-utils, ghostscript, pandoc, wkhtmltopdf, exiftool, and the python
# package fonttools
import os, re, sys, html, glob, shutil, filecmp, argparse, datetime, subprocess
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

# date formatting pleasantries (for title page, etc)
def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def run(cmd):
    if os.system(cmd) != 0:
        sys.exit('command failed: '+cmd)

def book_parts():
    return sorted(f.name for f in Path('./pdf').glob('*.pdf') if '.temp.' not in f.name)

def unite_book(output):
    subprocess.run(['pdfunite', *book_parts(), '../'+output], cwd='./pdf', check=True)

def page_count(pdf):
    out = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(next(l.split()[1] for l in out.splitlines() if l.startswith('Pages:')))

def ps_text(s):
    # UTF-16 hex string, so pdfmark titles survive parentheses and non-ASCII
    return '<FEFF'+s.encode('utf-16-be').hex().upper()+'>'

# set variables to passed parameters
parser = argparse.ArgumentParser()
parser.add_argument('-bo', '--book-only', '--fast', dest='book_only', action='store_true', help='Only generate title page & final recipe book, do not regenerate component recipes. (Fast mode)')
parser.add_argument('-a', '--all', '--slow', '--complete', '--regenerate', dest='regenerate_all', action='store_true', help='Regenerate all recipe PDFs, ignoring modified dates. (Slow mode)')
parser.set_defaults(book_only=False)
parser.set_defaults(regenerate_all=False)
args = parser.parse_args()

book_only=args.book_only
regenerate_all=args.regenerate_all

if book_only and regenerate_all:
    print('--all argument overrides --book_only!')
    book_only=False
elif regenerate_all:
    print('--all option selected')
elif book_only:
    print('--book-only option selected')


author = 'fexofenadine'
title = 'gitFOOD Recipe Book'
license_url = 'https://raw.githubusercontent.com/fexofenadine/gitfood/main/LICENSE'
repo_url = 'https://github.com/fexofenadine/gitfood'
site_url = 'https://fexofenadine.github.io/gitfood/'
site_url_short = 'https://foodgit.github.io'
margin_size = '15'
font_name = 'Nunito ExtraBold'
font_postscript_name = 'Nunito-ExtraBold'

#unused for now
# def optimize_pdf(recipe_name):
#     print('optimizing ./pdf/'+recipe_name+'.pdf for printing')
#     os.system('cd ./pdf && ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+recipe_name+'.temp.pdf ./'+recipe_name+'.pdf')

# def cleanup_tempfiles():
#     os.remove('./pdf/_title_page.md')
#     for f in glob.glob("./pdf/*.temp.pdf"):
#         os.remove(f)
#     for f in glob.glob("./recipes/*.temp.md"):
#         os.remove(f)
    
#get project version number
with open('./version.txt') as f:
    version_number = f.readline().strip('\n').strip()
print('version '+version_number+' detected')

#get license
with open('./LICENSE') as f:
    license_text = f.read().strip('\n').strip()

# toolchain (pandoc, wkhtmltopdf with patched qt, ghostscript, poppler-utils,
# exiftool) is installed by .github/workflows/build-book.yml; the font ships
# with the repo and is installed here so local and CI builds match
font_file = Path('./assets/fonts/nunito-extrabold.ttf')
font_dest = Path.home()/'.local/share/fonts'/font_file.name
if not font_dest.exists() or not filecmp.cmp(font_file, font_dest, shallow=False):
    print("installing font "+font_file.name)
    font_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(font_file, font_dest)
    run('fc-cache -f')
if font_name not in subprocess.run(['fc-list'], capture_output=True, text=True).stdout:
    sys.exit('font "'+font_name+'" not found by fontconfig')

# smart shrinking is disabled so the sizes in print-style.html are the printed sizes
pandoc_pdf_opts = ('-f gfm --quiet -t html5 --pdf-engine=wkhtmltopdf '
    '--pdf-engine-opt=--enable-local-file-access --pdf-engine-opt=--disable-smart-shrinking '
    '-V papersize:a4 -V margin-top=15mm -V margin-bottom=15mm -V margin-left=15mm -V margin-right=15mm '
    '-V mainfont:"'+font_name+'" -H "'+str(Path('./pdf/print-style.html').resolve())+'"')

print("generating title page")
with open("./pdf/0_3_title_page.stub") as f:
    title_page_body = f.read()
title_page_body = title_page_body.replace("{version_number}", version_number)
title_page_body = title_page_body.replace("{date}", custom_strftime('{S} of %B, %Y', datetime.datetime.now()))
output_file = Path("./pdf/0_3_title_page.md")
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text(title_page_body)
run('cd ./pdf && pandoc '+pandoc_pdf_opts+' ./0_3_title_page.md -o ./0_3_title_page.pdf')
os.remove('./pdf/0_3_title_page.md')

if book_only:
    print("only generating recipe book, skipping regeneration of individual recipes")
else:
    print("regenerating recipe pdfs from source")

    content_dir='./recipes'
    all_recipe_mds=[]
        
    recipe_mds=glob.glob(content_dir+'/*.md')
    all_recipe_mds=all_recipe_mds+recipe_mds
    print("Recipe(s) found: \""+str(all_recipe_mds)+"\"")
    for recipe_md in list(all_recipe_mds):
        tempfile = recipe_md[:-2]+"temp.md"
        recipe_name=Path(recipe_md).stem
        print('\nprocessing '+recipe_name)
        tag_file=content_dir+'/'+recipe_name+'/tags.txt'
        try: 
            if os.path.isfile(tag_file):
                with open(tag_file) as f:
                    tags = f.read().splitlines()
                    if not tags:
                        tags=[ "none" ]
            else:
                tags=[ "none" ]            
        except:
            tags=[ "none" ]
        finally:
            f.close()
        if 'snack' in list(tags):
            category=('1','snacks')
        elif 'breakfast' in list(tags):
            category=('2','breakfast')
        elif 'lunch' in list(tags):
            category=('3','lunch')
        elif 'dinner' in list(tags):
            category=('4','dinner')
        elif 'dessert' in list(tags):
            category=('5','dessert')
        elif 'sides' in list(tags):
            category=('6','sides')
        else:
            category=('9','extra stuff')
        print('primary category '+category[0]+' ['+category[1]+'] detected in tag file')
        try:
            recipe_md_modified=os.path.getmtime(recipe_md)
            recipe_pdf_modified=os.path.getmtime('./pdf/'+category[0]+'_'+recipe_name+'.pdf')
        except:
            # regenerate pdf if a file is missing (ie. if it hasn't been created yet)
            recipe_md_modified=1
            recipe_pdf_modified=0
        print("recipe modified: "+datetime.date.fromtimestamp(recipe_md_modified).isoformat()+"\npdf modified: "+datetime.date.fromtimestamp(recipe_pdf_modified).isoformat())
        # ignore modified dates if --all flag is set
        if regenerate_all:
            recipe_md_modified=1
            recipe_pdf_modified=0
        if recipe_md_modified > recipe_pdf_modified:
            print("recipe has been updated, regenerating pdf")
            #remove branding and pagecounts from footer
            delete_list = ["logo_sm.png", "count.svg"]
            with open(recipe_md) as fin, open(tempfile, "w+") as fout:
                for line in fin:
                    for word in delete_list:
                        if word in line:
                            line = ""
                            print("snipped "+word+" from "+tempfile)
                            break
                    fout.write(line)
            
            #generate pdf of recipe
            print('exporting to ./pdf/'+recipe_name+'.temp.pdf')
            run('cd ./recipes && pandoc '+pandoc_pdf_opts+' --dpi 70 ./'+recipe_name+'.temp.md -o ../pdf/'+recipe_name+'.temp.pdf')
            print('optimizing ./pdf/'+recipe_name+'.pdf for printing')
            run('cd ./pdf && ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+category[0]+'_'+recipe_name+'.pdf ./'+recipe_name+'.temp.pdf')
            # print('setting margin size to '+margin_size+'.')
            # os.system('cd ./pdf && pdfcrop --margins \''+margin_size+'\' ./'+category[0]+'_'+recipe_name+'.pdf ./'+category[0]+'_'+recipe_name+'.pdf')


            print('removing temp files')
            try:
                os.remove('./pdf/'+recipe_name+'.temp.pdf')
                os.remove(tempfile)
            except:
                pass
        else:
            print("pdf is newer, skipping")

# generate full book (all recipes) use pdfunite to include title page & pagebreaks
print("\nexporting Recipe Book")
tempfilename=title.replace(" ","_")+'.temp.pdf'
filename=title.replace(" ","_")+'.pdf'
category_names = {'1':'snacks', '2':'breakfast', '3':'lunch', '4':'dinner',
                  '5':'dessert', '6':'sides', '9':'extra stuff'}

# covers, the blank page and chapter dividers are simple enough to draw on every
# build, which also keeps the back cover's year current
static_page_css = '''
html, body { margin: 0; padding: 0; background: white; }
.page { position: relative; width: 210mm; height: 297mm; overflow: hidden;
        font-family: "'''+font_name+'''"; }
.gradient { background: #000;
            background: -webkit-gradient(linear, left top, left bottom, from(#3366cc), to(#000000)); }
.logo { position: absolute; left: 3.9mm; top: 123.8mm; width: 204.6mm; }
.welcome { position: absolute; left: 6.4mm; top: 119.5mm; font-size: 22pt; line-height: 1; color: #151515; }
.copyright { position: absolute; left: 0; right: 0; bottom: 12.3mm; text-align: center;
             font-size: 18pt; line-height: 1; color: #00ffff; }
'''

def text_outline(text, size):
    """SVG path data for text set in the book font, and its advance width (in pt)"""
    font = TTFont(font_file)
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    scale = size / font['head'].unitsPerEm
    pen, x = SVGPathPen(glyphs), 0
    for ch in text:
        name = cmap.get(ord(ch))
        if name:
            glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
            x += glyphs[name].width * scale
    return pen.getCommands(), x

def divider_svg(text):
    # drawn as a single outline shape, filled and stroked: wkhtmltopdf drops CSS
    # text-stroke/text-shadow, and SVG <text> lays the fill and stroke out separately
    # so they drift apart along the word
    path, width = text_outline(text, 74)
    return ('<svg width="210mm" height="297mm" viewBox="0 0 595 842">'
            '<path transform="translate(%.2f 447)" d="%s" fill="#6bade9" stroke="#3a5e7a" '
            'stroke-width="1.1" stroke-linejoin="round"/></svg>') % (297.6 - width/2, path)

def static_page(name, body, dark=False):
    src = Path('./pdf')/(name+'.temp.html')
    src.write_text('<!doctype html><html><head><meta charset="utf-8"><style>'+static_page_css+
                   ('html, body { background: #000; }' if dark else '')+
                   '</style></head><body>'+body+'</body></html>')
    subprocess.run(['wkhtmltopdf', '--quiet', '--enable-local-file-access', '--disable-smart-shrinking',
                    '-s', 'A4', '-T', '0', '-B', '0', '-L', '0', '-R', '0',
                    str(src), str(Path('./pdf')/(name+'.pdf'))], check=True)
    src.unlink()

print("generating covers, blank page and chapter dividers")
for old in Path('./pdf').glob('[0-9]__*.pdf'):
    old.unlink()
static_page('0_1_cover', '<div class="page gradient"><img class="logo" src="'+
            str(Path('./images/logo_md.png').resolve())+'"><div class="welcome">welcome to</div></div>', dark=True)
static_page('0_2_blank', '<div class="page"></div>')
static_page('zzzzz_cover', '<div class="page gradient"><div class="copyright">&copy; gitFOOD '+
            str(datetime.datetime.now().year)+'</div></div>', dark=True)
used_categories = sorted({f.name[0] for f in Path('./pdf').glob('[0-9]_[a-z]*.pdf')})
for num in used_categories:
    name = category_names.get(num, 'other')
    static_page(num+'__'+name.split()[0], '<div class="page">'+divider_svg(name)+'</div>')

def recipe_title(part):
    md = Path('./recipes')/(part.split('_', 1)[1][:-4]+'.md')
    if md.exists():
        for line in md.read_text().splitlines():
            if line.startswith('# '):
                return line[2:].strip()
    return md.stem

def layout():
    """first page of each part, pages to number (recipes and blanks), and the
    category/recipe outline, all as page numbers in the finished book"""
    start, page, numbered, sections = {}, 1, set(), []
    for part in book_parts():
        n = page_count(Path('./pdf')/part)
        start[part] = page
        divider = re.match(r'(\d)__', part)
        if divider:
            sections.append((category_names.get(divider[1], part[3:-4]), page, []))
        elif re.match(r'\d_[a-z]', part):
            numbered.update(range(page, page+n))
            if sections:
                sections[-1][2].append((recipe_title(part), page))
        elif part == '0_2_blank.pdf' or part.startswith('zzzzz_blank'):
            numbered.update(range(page, page+n))
        page += n
    return start, numbered, sections

def build_contents(sections):
    rows = ['# contents', '']
    for name, _, recipes in sections:
        if recipes:
            rows.append('<h2 class="toc-category">'+html.escape(name)+'</h2>')
            rows.append('<table class="toc">')
            rows += ['<tr><td>'+html.escape(t)+'</td><td class="toc-page">'+str(pg)+'</td></tr>' for t, pg in recipes]
            rows += ['</table>', '']
    Path('./pdf/0_4_contents.md').write_text('\n'.join(rows))
    run('cd ./pdf && pandoc '+pandoc_pdf_opts+' ./0_4_contents.md -o ./0_4_contents.pdf')
    os.remove('./pdf/0_4_contents.md')

# the contents page's own length shifts every later page, so build it once to
# learn its length, then again with the final page numbers
print("generating contents page")
Path('./pdf/0_4_contents.pdf').unlink(missing_ok=True)
build_contents(layout()[2])
start, numbered, sections = layout()
build_contents(sections)
if layout()[2] != sections:
    sys.exit('contents page length changed between passes')

unite_book(tempfilename)

# calculate and insert number of blank pages to insert for tidy booklet printing
p1 = subprocess.Popen(['pdfinfo', tempfilename], stdout=subprocess.PIPE)
p2 = subprocess.Popen(['grep', 'Pages'], stdin=p1.stdout, stdout=subprocess.PIPE)
p3 = subprocess.Popen(['sed', 's/[^0-9]*//'], stdin=p2.stdout, stdout=subprocess.PIPE)
pagecount=p3.communicate()[0].decode("utf-8")
print('pagecount: '+pagecount)
num_add_pages=(4 - int(pagecount) % 4) % 4
print('number of pages to insert: '+str(num_add_pages))
for i in range(0, num_add_pages):
    shutil.copyfile('./pdf/0_2_blank.pdf', f'./pdf/zzzzz_blank{i}.pdf')

# regenerate the book with the additional pages
if num_add_pages > 0:
    print('regenerating book with extra padding for booklet printing')
    unite_book(tempfilename)
    # the padding pages are numbered too
    numbered = layout()[1]

print('optimizing '+filename+' for printing')
# bookmarks (sidebar outline) and page numbers on recipe and blank pages, added in the same pass
marks = ['[/Title '+ps_text('contents')+' /Page '+str(start['0_4_contents.pdf'])+' /OUT pdfmark']
for name, page, recipes in sections:
    if recipes:
        marks.append('[/Title %s /Page %d /Count -%d /OUT pdfmark' % (ps_text(name), page, len(recipes)))
        marks += ['[/Title %s /Page %d /OUT pdfmark' % (ps_text(t), pg) for t, pg in recipes]
marks.append('[/PageMode /UseOutlines /DOCVIEW pdfmark')
Path('./bookmarks.temp.ps').write_text('\n'.join(marks)+'\n')
number_pages = ('/NumberedPages << '+' '.join('%d true' % n for n in sorted(numbered))+' >> def '
    '<< /EndPage { exch 1 add exch 0 eq '
    '{ dup NumberedPages exch known '
    '{ /'+font_postscript_name+' findfont 10 scalefont setfont 0.45 setgray '
    '20 string cvs dup stringwidth pop 2 div 297.64 exch sub 22 moveto show } { pop } ifelse true } '
    '{ pop false } ifelse } bind >> setpagedevice')
subprocess.run(['ghostscript', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/printer',
    '-dNOPAUSE', '-dQUIET', '-dBATCH', '-sFONTPATH='+str(font_dest.parent),
    '-sOutputFile=./'+filename, '-c', number_pages, '-f', './'+tempfilename, './bookmarks.temp.ps'], check=True)
os.remove('./bookmarks.temp.ps')

# cleanup
print('removing temp file '+tempfilename)
os.remove('./'+tempfilename)
print('removing blank padding pages')
for f in glob.glob("./pdf/zzzzz_blank*.pdf"):
    os.remove(f)

print("applying metadata")
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y:%m:%d %H:%M:%S+00:00')
description = (title+' '+version_number+', a collection of recipes from '+site_url+
               ' (also '+site_url_short+'). Formatted for A4 and booklet printing.')
keywords = ['gitFOOD', 'recipes', 'recipe book', 'cookbook',
            'snacks', 'breakfast', 'lunch', 'dinner', 'dessert', 'sides']
subprocess.run(['exiftool', '-overwrite_original', '-q',
    '-PDF:Title='+title, '-XMP-dc:Title='+title,
    '-PDF:Author='+author, '-XMP-dc:Creator='+author, '-XMP-dc:Publisher='+author,
    '-PDF:Subject='+description, '-XMP-dc:Description='+description,
    '-PDF:Keywords='+', '.join(keywords), '-XMP-pdf:Keywords='+', '.join(keywords),
    *['-XMP-dc:Subject='+k for k in keywords],
    '-PDF:Creator=gitFOOD generate_pdfs.py (pandoc, wkhtmltopdf)',
    '-XMP-xmp:CreatorTool=gitFOOD generate_pdfs.py (pandoc, wkhtmltopdf)',
    '-PDF:CreateDate='+now, '-PDF:ModifyDate='+now,
    '-XMP-xmp:CreateDate='+now, '-XMP-xmp:ModifyDate='+now, '-XMP-dc:Date='+now,
    '-XMP-dc:Identifier='+title+' '+version_number,
    '-XMP-dc:Language=en',
    '-XMP-dc:Source='+repo_url,
    '-XMP-dc:Relation='+site_url, '-XMP-dc:Relation='+site_url_short,
    '-XMP-dc:Rights=GNU General Public License v3.0',
    '-XMP-xmpRights:Marked=True', '-XMP-xmpRights:WebStatement='+license_url,
    './'+filename], check=True)
