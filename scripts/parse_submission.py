import re
import shutil
import sys
from math import ceil
from pathlib import Path
import requests

def get_image(image):
    print("downloading "+image["location"])
    response = requests.get(image["url"], stream=True)
    if response.status_code == 200:
        with open(image["location"], 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response

script_name = sys.argv[0]
# take raw text or file path as argument
if sys.argv[1][:3]=="###":
    issue_body = sys.argv[1]
else:
    with open(sys.argv[1]) as f:
        issue_body = f.read()

recipe_title=issue_body.split("### ")[1].split("\n")[2]
friendly_title=re.sub(r'[^a-z0-9]', '', recipe_title.lower())

# print("Friendly title: "+friendly_title)

output_file = Path("submissions/"+friendly_title+"/images/.gitkeep")
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text("placeholder text")

recipe_file_name="submissions/"+friendly_title+"/"+friendly_title+".raw"
output_file = Path(recipe_file_name)
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text(issue_body)

image_links=re.findall(r'!\[[^\]]*\]\((.*?)\s*?\s*\)', issue_body)

if image_links:
    images=[]
    i=0
    for image_link in image_links:
        if i==0:
            image_name="main.jpg"
        else:
            image_name=str(i)+".jpg"
        i=i+1
        image={
            "tag":"{"+image_name+"}",
            "location":"submissions/"+friendly_title+"/images/"+image_name,
            "url":image_link
        }
        images.append(image)
        get_image(image)

def section(label):
    """the answer under a '### label' heading of the issue form ('' if left empty)"""
    parts = issue_body.split("### "+label)
    if len(parts) < 2:
        return ""
    text = parts[1].split("### ")[0].strip()
    return "" if text == "_No response_" else text

def listed(text, marker):
    # one list item per non-blank line; blank lines between entries (which the form
    # used to ask for) previously became empty list items
    return "\n".join(marker+line.strip() for line in text.splitlines() if line.strip())

with open(recipe_file_name,'r') as f:
    body_lines = f.readlines()
tags=[]
for line in body_lines:
    if line[:6].lower()=="- [x] ":
        tag=line[6:].strip().lower().replace(" ","_")
        tags.append(tag)

tags += [t.strip().lower().replace(" ","_") for t in section("Additional tags").split(",")]
tags.append(section("How difficult is it to prepare this meal?").lower())
# drop blanks and duplicates
tags=sorted({tag for tag in tags if tag})
print("saving submissions/"+friendly_title+"/tags.txt")
with open("submissions/"+friendly_title+"/tags.txt", 'w') as f:
    f.write('\n'.join(map(str, tags)))

# heading syntax
### Title of Recipe
### Ingredients
### Method
### Tips

out_title="# "+recipe_title+"\n"
out_ingredients="## Ingredients\n\n"+listed(section("Ingredients"), "- ")+"\n"
out_method="## Method\n\n"+listed(section("Method"), "> 1. ")+"\n"
tips_text=section("Tips")
out_tips="## Tips\n\n"+listed(tips_text, "> - ")+"\n" if tips_text else ""
serves=section("How many people does it serve?")
out_serves="**Serves:** "+serves+"\n" if serves else ""

output=[out_title, out_ingredients, out_method, out_tips, out_serves]
try:
    images
except NameError:
    pass
else:
    output.insert(0, "\n")

formatted_output="\n".join(output)

numlines = formatted_output.count('\n')

try:
    images
except NameError:
    print("no images attached")
else:
    print("embedding images")
    numimages = len(images)
    image_spacing=ceil(numlines / numimages)
    lines=formatted_output.splitlines()
    print("embedding image tags")
    i=0
    for image in images:
        lines[i*image_spacing]=lines[i*image_spacing]+" "+image["tag"]
        i=i+1
    formatted_output="\n".join(lines)

print("saving submissions/"+friendly_title+"/"+friendly_title+".recipe")
with open("submissions/"+friendly_title+"/"+friendly_title+".recipe", 'w') as f:
    f.write(formatted_output)
#print("\n".join(output))

if Path("recipes/"+friendly_title).exists():
        shutil.rmtree("recipes/"+friendly_title)
shutil.copytree("submissions/"+friendly_title , "recipes/"+friendly_title ,ignore=shutil.ignore_patterns("*.raw"))

exec(open("scripts/generate_markdown_recipes.py").read())
