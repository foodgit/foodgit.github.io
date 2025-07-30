import os, glob, shutil, filecmp
from pathlib import Path

content_dir='./recipes'
all_recipe_stubs=[ "./template/template/template.recipe" ]
recipe_dirs=next(os.walk(content_dir))[1]
for recipe_dir in list(recipe_dirs):
    recipe_stubs=glob.glob(content_dir+'/'+recipe_dir+'/*.recipe')
    all_recipe_stubs=all_recipe_stubs+recipe_stubs
print("Recipe stub(s) found: \""+str(all_recipe_stubs)+"\"")
for recipe_stub in list(all_recipe_stubs):
    with open(recipe_stub) as f:
        recipe_body = f.read()
    image_dir="./"+recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-2]+"/images/"
    image_dir_new="./"+recipe_stub.split("/")[-2]+"/images/"
    image_files = glob.glob(image_dir+"*.jpg")
    print("Image(s) found: "+str(image_files))
    for image_file in list(image_files):
        image_file=str(image_file).split("/")[-1]
        image_path=image_dir_new.replace("./","")+image_file
        if image_file == "main.jpg":
            image_width="55%"
        else:
            image_width="35%"
        recipe_body = recipe_body.replace("{"+image_file+"}", "<img src=\""+image_path+"\" width=\""+image_width+"\" align=\"right\" />")
    tag_file="./"+recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-2]+"/tags.txt"
    tags=list()
    formatted_tags=list()
    try: 
        if os.path.isfile(tag_file):
            with open(tag_file) as f:
                tags = f.read().splitlines()
                if not tags:
                    tags=[ "none" ]
                else:
                    tags.sort()
        else:
            tags=[ "none" ]            
    except:
        tags=[ "none" ]
    finally:
        f.close()
    taglinks=""
    for tag in list(tags):
        taglinks=taglinks+'<img src="https://img.shields.io/badge/'+tag+'-blue.svg" /> '
    temp_file_name="working/"+recipe_stub.split("/")[-1].replace(".recipe",".md")
    recipe_file_name=recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-1].replace(".recipe",".md")
    
    output_file = Path(temp_file_name)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    output_file.write_text(recipe_body)

    with open(temp_file_name, "a") as f:
        f.write('\n\n<img src="../images/logo_sm.png" width="40%" />')
        f.write('\n\n'+taglinks)
        #pageviews
        #f.write('\n\n<p>This page has been viewed <span id="counter">...</span> times.</p>')
        f.write('\n\n<script data-goatcounter="https://fexofenadine.goatcounter.com/count"\n\tasync src="//gc.zgo.at/count.js"></script>')

    try:
        identical=filecmp.cmp(temp_file_name,recipe_file_name)
    except FileNotFoundError:
        print("New recipe found! Creating "+recipe_file_name)
        shutil.copyfile(temp_file_name, recipe_file_name)
    except:
        print("something went wrong comparing temp file with destination")
    if not identical:
        print(recipe_file_name+" has been updated. Replacing with new version.")
        shutil.copyfile(temp_file_name, recipe_file_name)
    else:
        print(recipe_file_name+" has not been modified.")
shutil.rmtree("working")