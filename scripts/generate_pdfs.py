# linux only for now
import os, glob, shutil, filecmp, argparse, datetime, subprocess
from pathlib import Path

# date formatting pleasantries (for title page, etc)
def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

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
    print("--all argument overrides --book_only!")
    book_only=False
elif regenerate_all:
    print("--all option selected")
elif book_only:
    print("--book-only option selected")


author = "fexofenadine"
title = "gitFOOD Recipe Book"
license_url = "https://raw.githubusercontent.com/fexofenadine/gitfood/main/LICENSE"

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
with open("./version.txt") as f:
    version_number = f.readline().strip('\n').strip()
print("version "+version_number+" detected")

#get license
with open("./LICENSE") as f:
    license_text = f.read().strip('\n').strip()

# print("installing pandoc")
# os.system('wget https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-1-amd64.deb -P ~ && sudo dpkg -i ~/pandoc-3.1.8-1-amd64.deb && rm ~/pandoc-3.1.8-1-amd64.deb')

# print("installing font")
# os.system('cp ./fonts/helvetica-rounded-bold.otf ~/.local/share/fonts/helvetica-rounded-bold.otf')

print("generating title page")
with open("./pdf/0_3_title_page.stub") as f:
    title_page_body = f.read()
title_page_body = title_page_body.replace("{version_number}", version_number)
title_page_body = title_page_body.replace("{date}", custom_strftime('{S} of %B, %Y', datetime.datetime.now()))
output_file = Path("./pdf/0_3_title_page.md")
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text(title_page_body)
os.system('cd ./pdf && pandoc --quiet -f gfm -t html5 -V papersize:a4 -V geometry:margin=2cm -V mainfont:"Helvetica Rounded" -V documentclass=book --pdf-engine-opt=--enable-local-file-access ./0_3_title_page.md -o ./0_3_title_page.pdf')
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
            os.system('cd ./recipes && pandoc -f gfm --quiet -t html5 -V papersize:a4 -V geometry:margin=2cm -V mainfont:"Helvetica Rounded" -V mainfontoptions:"Scale=1.1" -V fontsize=20pt -V documentclass=book --pdf-engine-opt=--enable-local-file-access --dpi 70 ./'+recipe_name+'.temp.md -o ../pdf/'+recipe_name+'.temp.pdf')
            print('optimizing ./pdf/'+recipe_name+'.pdf for printing')
            os.system('cd ./pdf && ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+category[0]+'_'+recipe_name+'.pdf ./'+recipe_name+'.temp.pdf')

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
os.system('cd ./pdf && pdfunite *.pdf ../'+tempfilename)

# calculate and insert number of blank pages to insert for tidy booklet printing
p1 = subprocess.Popen(['pdfinfo', tempfilename], stdout=subprocess.PIPE)
p2 = subprocess.Popen(['grep', 'Pages'], stdin=p1.stdout, stdout=subprocess.PIPE)
p3 = subprocess.Popen(['sed', 's/[^0-9]*//'], stdin=p2.stdout, stdout=subprocess.PIPE)
pagecount=p3.communicate()[0].decode("utf-8")
print('pagecount: '+pagecount)
num_add_pages=4 - (int(pagecount) % 4)
print('number of pages to insert: '+str(num_add_pages))
for i in range(0, num_add_pages):
    shutil.copyfile('./pdf/0_2_blank.pdf', f'./pdf/zzzzz_blank{i}.pdf')

# regenerate the book with the additional pages
if num_add_pages > 0:
    print('regenerating book with extra padding for booklet printing')
    os.system('cd ./pdf && pdfunite *.pdf ../'+tempfilename)

print('optimizing '+filename+' for printing')
os.system('ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+filename+' ./'+tempfilename)

# cleanup
print('removing temp file '+tempfilename)
os.remove('./'+tempfilename)
print('removing blank padding pages')
for f in glob.glob("./pdf/zzzzz_blank*.pdf"):
    os.remove(f)

print("applying metadata")
os.system('exiftool -overwrite_original -author="'+author+'" -xmp-dc:creator="'+author+'" -marked="True" -webstatement="'+license_url+'" -description="'+title+' '+version_number+'\nhttps://foodgit.gihub.io" -xmp-dc:description="'+title+' '+version_number+'\nhttps://foodgit.gihub.io" -title="'+title+'" -xmp-dc:title="'+title+'" ./'+filename)