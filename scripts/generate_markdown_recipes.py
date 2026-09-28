import shutil, filecmp, subprocess, datetime, html
from pathlib import Path

def get_dates(stub_path):
    """Returns (last_updated, created) ISO dates from the stub's git history."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%as", "--", str(stub_path)],
            capture_output=True, text=True, check=True
        )
        dates = result.stdout.strip().splitlines()
        if not dates:
            return "", ""
        return dates[0], dates[-1]
    except Exception:
        return "", ""

def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def humanize_date(iso_date):
    if not iso_date:
        return ""
    d = datetime.datetime.strptime(iso_date, "%Y-%m-%d")
    return d.strftime('{S} of %B %Y').replace('{S}', str(d.day)+suffix(d.day))

content_dir = Path("recipes")
all_recipe_stubs = [Path("template/template/template.recipe")]
for recipe_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
    all_recipe_stubs += sorted(recipe_dir.glob("*.recipe"))
print("Recipe stub(s) found: \""+str(all_recipe_stubs)+"\"")

for recipe_stub in all_recipe_stubs:
    recipe_body = recipe_stub.read_text()
    recipe_dir = recipe_stub.parent
    content_root = recipe_dir.parent

    lines = recipe_body.splitlines()
    title_idx = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
    title = lines[title_idx][2:].strip() if title_idx is not None else recipe_stub.stem
    main_idx = next((i for i, l in enumerate(lines) if l.strip() == "{main.jpg}"), None)
    # title must be the first line for jekyll-titles-from-headings to name the page
    if main_idx is not None and title_idx is not None and main_idx < title_idx:
        lines.pop(main_idx)
        title_idx -= 1
        lines[title_idx+1:title_idx+1] = ["", "{main.jpg}"]
        recipe_body = "\n".join(lines).lstrip("\n")

    image_dir = recipe_dir/"images"
    image_files = sorted(image_dir.glob("*.jpg"))
    print("Image(s) found: "+str(image_files))
    for image_file in image_files:
        image_path = recipe_dir.name+"/images/"+image_file.name
        if image_file.name == "main.jpg":
            image_width="55%"
            image_alt=title
        else:
            image_width="35%"
            image_alt=title+" - photo "+image_file.stem
        recipe_body = recipe_body.replace("{"+image_file.name+"}", "<img src=\""+image_path+"\" alt=\""+html.escape(image_alt)+"\" width=\""+image_width+"\" align=\"right\" />")
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
        taglinks=taglinks+'<img src="https://img.shields.io/badge/'+tag+'-blue.svg" alt="'+tag+'" /> '
    temp_file_name = Path("working")/recipe_stub.with_suffix(".md").name
    recipe_file_name = content_root/recipe_stub.with_suffix(".md").name

    output_file = temp_file_name
    output_file.parent.mkdir(exist_ok=True, parents=True)
    output_file.write_text(recipe_body)

    last_updated_iso, created_iso = get_dates(recipe_stub)
    last_updated = humanize_date(last_updated_iso)
    created = humanize_date(created_iso)

    with open(temp_file_name, "a") as f:
        f.write('\n\n<img src="../images/logo_sm.png" alt="gitFOOD logo" width="40%" />')
        f.write('\n\n'+taglinks)
        f.write('\n\n*Created: '+created+'*')
        f.write('\n\n*Last Updated: '+last_updated+'*')

    try:
        identical=filecmp.cmp(temp_file_name,recipe_file_name)
    except FileNotFoundError:
        print("New recipe found! Creating "+str(recipe_file_name))
        identical=False
    except:
        print("something went wrong comparing temp file with destination")
        identical=False
    if not identical:
        print(str(recipe_file_name)+" has been updated. Replacing with new version.")
        shutil.copyfile(temp_file_name, recipe_file_name)
    else:
        print(str(recipe_file_name)+" has not been modified.")
shutil.rmtree("working")
