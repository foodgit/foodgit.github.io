# linux only for now
import os, glob, shutil, filecmp, argparse, datetime
from pathlib import Path

# date formatting pleasantries (for title page, etc)
def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

parser = argparse.ArgumentParser()
parser.add_argument('-bo', '--book-only', '-fast', dest='book_only', action='store_true', help='Only generate title page & final recipe book, do not regenerate component recipes. (Fast mode)')
parser.set_defaults(book_only=False)
args = parser.parse_args()

book_only=args.book_only

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
with open("./pdf/_3_title_page.stub") as f:
    title_page_body = f.read()
title_page_body = title_page_body.replace("{version_number}", version_number)
title_page_body = title_page_body.replace("{date}", custom_strftime('{S} of %B, %Y', datetime.datetime.now()))
output_file = Path("./pdf/_3_title_page.md")
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text(title_page_body)
os.system('cd ./pdf && pandoc --quiet -f gfm -t html5 -V papersize:a4 -V geometry:margin=2cm -V mainfont:"Helvetica Rounded" -V documentclass=book --pdf-engine-opt=--enable-local-file-access ./_3_title_page.md -o ./_3_title_page.pdf')
os.remove('./pdf/_3_title_page.md')

if book_only:
    print("only generating recipe book, skipping regeneration of individual recipes")
else:
    print("regenerating all recipe pdfs from source")

    content_dir='./recipes'
    all_recipe_mds=[]
        
    recipe_mds=glob.glob(content_dir+'/*.md')
    all_recipe_mds=all_recipe_mds+recipe_mds
    print("Recipe(s) found: \""+str(all_recipe_mds)+"\"")
    for recipe_md in list(all_recipe_mds):
        tempfile = recipe_md[:-2]+"temp.md"
        recipe_name=Path(recipe_md).stem
        print('\nprocessing '+recipe_name)

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
        os.system('cd ./pdf && ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+recipe_name+'.pdf ./'+recipe_name+'.temp.pdf')

        print('removing temp files')
        try:
            os.remove('./pdf/'+recipe_name+'.temp.pdf')
            os.remove(tempfile)
        except:
            pass

# generate full book (all recipes) use pdfunite to include title page & pagebreaks
print("\nexporting Recipe Book")
tempfilename=title.replace(" ","_")+'.temp.pdf'
filename=title.replace(" ","_")+'.pdf'
os.system('cd ./pdf && pdfunite *.pdf ../'+tempfilename)

print('optimizing '+filename+' for printing')
os.system('ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+filename+' ./'+tempfilename)
os.remove('./'+tempfilename)

print("applying metadata")
os.system('exiftool -overwrite_original -author="'+author+'" -xmp-dc:creator="'+author+'" -marked="True" -webstatement="'+license_url+'" -description="'+title+' '+version_number+'\nhttps://foodgit.gihub.io" -xmp-dc:description="'+title+' '+version_number+'\nhttps://foodgit.gihub.io" -title="'+title+'" -xmp-dc:title="'+title+'" ./'+filename)