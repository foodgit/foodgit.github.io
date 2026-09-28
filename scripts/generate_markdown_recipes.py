import shutil, filecmp, subprocess
from pathlib import Path

def get_last_updated(stub_path):
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%as", "--", str(stub_path)],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return ""

content_dir = Path("recipes")
all_recipe_stubs = [Path("template/template/template.recipe")]
for recipe_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
    all_recipe_stubs += sorted(recipe_dir.glob("*.recipe"))
print("Recipe stub(s) found: \""+str(all_recipe_stubs)+"\"")

for recipe_stub in all_recipe_stubs:
    recipe_body = recipe_stub.read_text()
    recipe_dir = recipe_stub.parent
    content_root = recipe_dir.parent
    image_dir = recipe_dir/"images"
    image_files = sorted(image_dir.glob("*.jpg"))
    print("Image(s) found: "+str(image_files))
    for image_file in image_files:
        image_path = recipe_dir.name+"/images/"+image_file.name
        if image_file.name == "main.jpg":
            image_width="55%"
        else:
            image_width="35%"
        recipe_body = recipe_body.replace("{"+image_file.name+"}", "<img src=\""+image_path+"\" width=\""+image_width+"\" align=\"right\" />")
    tag_file = recipe_dir/"tags.txt"
    tags=list()
    formatted_tags=list()
    try:
        if tag_file.is_file():
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
    temp_file_name = Path("working")/recipe_stub.with_suffix(".md").name
    recipe_file_name = content_root/recipe_stub.with_suffix(".md").name

    output_file = temp_file_name
    output_file.parent.mkdir(exist_ok=True, parents=True)
    output_file.write_text(recipe_body)

    last_updated = get_last_updated(recipe_stub)

    with open(temp_file_name, "a") as f:
        f.write('\n\n<img src="../images/logo_sm.png" width="40%" />')
        f.write('\n\n'+taglinks)
        f.write('\n\n*Last Updated: '+last_updated+'*')
        #pageviews
        #f.write('\n\n<p>This page has been viewed <span id="counter">...</span> times.</p>')
        #f.write('\n\n<script data-goatcounter="https://fexofenadine.goatcounter.com/count"\n\tasync src="//gc.zgo.at/count.js"></script>')

    try:
        identical=filecmp.cmp(temp_file_name,recipe_file_name)
    except FileNotFoundError:
        print("New recipe found! Creating "+str(recipe_file_name))
        shutil.copyfile(temp_file_name, recipe_file_name)
    except:
        print("something went wrong comparing temp file with destination")
    if not identical:
        print(str(recipe_file_name)+" has been updated. Replacing with new version.")
        shutil.copyfile(temp_file_name, recipe_file_name)
    else:
        print(str(recipe_file_name)+" has not been modified.")
shutil.rmtree("working")
