import os, glob, shutil

content_dir='./recipes'
all_recipe_stubs=list()
recipe_dirs=next(os.walk(content_dir))[1]
for recipe_dir in list(recipe_dirs):
    print("Recipe folder found: \""+content_dir+"/"+recipe_dir+"\"")
    recipe_stubs=glob.glob(content_dir+'/'+recipe_dir+'/*.recipe')
    all_recipe_stubs=all_recipe_stubs+recipe_stubs
print("Recipe stub(s) found: \""+str(all_recipe_stubs)+"\"")
for recipe_stub in list(all_recipe_stubs):
    with open(recipe_stub) as f:
        recipe_body = f.read()
    #print(recipe_stub.split("/"))
    image_dir="./"+recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-2]+"/images/"
    image_dir_new="./"+recipe_stub.split("/")[-2]+"/images/"
    image_files = glob.glob(image_dir+"*.jpg")
    print("Image(s) found: "+str(image_files))
    for image_file in list(image_files):
        image_file=str(image_file).split("/")[-1]
    #   pure markdown image, no styling
    #   recipe_body = recipe_body.replace("{"+image_file+"}", "![]("+image_dir_new+image_file+")")
    #   try html styling instead
        image_path=image_dir_new.replace("./","")+image_file
        if image_file == "main.jpg":
            image_width="55%"
        else:
            image_width="33%"
    #    recipe_body = recipe_body.replace("{"+image_file+"}", "<img src=\"https://github.com/fexofenadine/gitfood/raw/main/recipes/"+image_path+"\" width=\"50%\" align=\"right\" />")
        recipe_body = recipe_body.replace("{"+image_file+"}", "<img src=\""+image_path+"\" width=\""+image_width+"\" align=\"right\" />")
    tag_file="./"+recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-2]+"/tags.txt"
    tags=list()
    formatted_tags=list()
    try: 
        if os.path.isfile(tag_file):
            with open(tag_file) as f:
                tags = f.read().splitlines()
    finally:
        f.close()
    #![Recipe: "+tag+""](https://img.shields.io/badge/recipe-"+tag+"-blue.svg)""
    #https://img.shields.io/badge/recipe-fast_food-blue.svg
    for tag in list(tags):
        formatted_tags=formatted_tags+["![Recipe: "+tag+"](https://img.shields.io/badge/tag-"+tag+"-blue.svg)"]
    print(formatted_tags)
    recipe_body = recipe_body.replace("{tags}", ' '.join(formatted_tags))
    recipe_file_name=recipe_stub.split("/")[-3]+"/"+recipe_stub.split("/")[-1].replace(".recipe",".md")
    with open(recipe_file_name,'w') as f:
        f.write(recipe_body)
