import os, glob, shutil

content_dir='./recipes'
all_recipe_stubs=[ "./template/template/template.recipe" ]
recipe_dirs=next(os.walk(content_dir))[1]
for recipe_dir in list(recipe_dirs):
#    print("Recipe folder found: \""+content_dir+"/"+recipe_dir+"\"")
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
            image_width="33%"
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
            tags=[ "none" ]            
    except:
        tags=[ "none" ]
    finally:
        f.close()
    for tag in list(tags):
        formatted_tags=formatted_tags+["![Recipe: "+tag+"](https://img.shields.io/badge/tag-"+tag+"-blue.svg)"]
    #replace {tag} with formatted tag images, no longer required
    #recipe_body = recipe_body.replace("{tags}", ' '.join(formatted_tags))
    recipe_file_name=recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-1].replace(".recipe",".md")
    with open(recipe_file_name,'w') as f:
        f.write(recipe_body)
    with open(recipe_file_name, "a") as f:
        f.write('&nbsp;\n&nbsp;\n&nbsp;\n&nbsp;\n<img src="../logo.png" width="33%" align="right" />&nbsp;\n&nbsp;\n&nbsp;\n&nbsp;\n<img src="https://profile-counter.glitch.me/fexofenadine_'+recipe_stub.split("/")[-2]+'/count.svg" height="20" align="right" />&nbsp;\n&nbsp;\n&nbsp;\n&nbsp;\n')
        f.write(' '.join(formatted_tags))
