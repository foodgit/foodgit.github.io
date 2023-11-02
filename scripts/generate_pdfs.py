# linux only for now
import os, glob, shutil, filecmp
from pathlib import Path

# print("installing pandoc")
# os.system('wget https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-1-amd64.deb -P ~ && sudo dpkg -i ~/pandoc-3.1.8-1-amd64.deb && rm ~/pandoc-3.1.8-1-amd64.deb')

# print("installing font")
# os.system('cp ./fonts/helvetica-rounded-bold.otf ~/.local/share/fonts/helvetica-rounded-bold.otf')

print("generating title page")
os.system('cd ./pdf && pandoc -f gfm -t html5 --metadata pagetitle="gitFood Recipe Book 1.0.1" -V mainfont:"Helvetica Rounded" -V documentclass=book --pdf-engine-opt=--enable-local-file-access ./_title_page.md -o ./_title_page.pdf')

content_dir='./recipes'
all_recipe_mds=[]
    
#recipe_dirs=next(os.walk(content_dir))[1]
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
    # --lua-filter=../scripts/noexport-subtrees.lua no longer required
    os.system('cd ./recipes && pandoc -f gfm --quiet -t html5 --metadata pagetitle="gitFOOD Recipe Book 1.0.1" -V papersize:a4 -V geometry:margin=2cm -V mainfont:"Helvetica Rounded" -V mainfontoptions:"Scale=1.1" -V fontsize=20pt -V documentclass=book --pdf-engine-opt=--enable-local-file-access --dpi 70 ./'+recipe_name+'.temp.md -o ../pdf/'+recipe_name+'.temp.pdf')
    print('optimizing ./pdf/'+recipe_name+'.pdf for printing')
    os.system('cd ./pdf && ghostscript -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=./'+recipe_name+'.pdf ./'+recipe_name+'.temp.pdf')
    print('removing temp files')
    os.remove('./pdf/'+recipe_name+'.temp.pdf')
    os.remove(tempfile)

# generate full book (all recipes) use pdfunite to include title page & pagebreaks
print("\nexporting Recipe Book")
os.system('cd ./pdf && pdfunite *.pdf ../gitFOOD_Recipe_Book.pdf')
