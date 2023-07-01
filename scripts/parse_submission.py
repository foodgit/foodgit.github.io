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
friendly_title=recipe_title.strip().replace(" ","").lower()

# print("Friendly title: "+friendly_title)

output_file = Path("submissions/"+friendly_title+"/images/.placeholder")
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

with open(recipe_file_name,'r') as f:
    body_lines = f.readlines()
read_nextline=False
tags=[]
for line in body_lines:
    if line[:6]=="- [X] ":
        tag=line[6:].strip().lower()
        tags.append(tag)

additional_tags=issue_body.split("### Additional tags")[1].split("\n")[2].lower().replace(", ",",").replace(" ","_").split(",")
tags=tags+additional_tags
print("saving submissions/"+friendly_title+"/tags.txt")
with open("submissions/"+friendly_title+"/tags.txt", 'w') as f:
    f.write('\n'.join(map(str, tags)))

# heading syntax
### Title of Recipe
### Ingredients
### Method
### Tips

out_title="# "+recipe_title+"\n"

ingredients_text=issue_body.split("### Ingredients")[1].split("### ")[0].strip()
ingredients_text="- ".join(("\n"+ingredients_text.lstrip()).splitlines(True))
out_ingredients="## Ingredients:\n"+ingredients_text+"\n"

method_text=issue_body.split("### Method")[1].split("### ")[0].strip()
method_text="> ".join(("\n"+method_text.lstrip()).splitlines(True))
out_method="## Method:\n"+method_text+"\n"

tips_text=issue_body.split("### Tips")[1].split("### ")[0].strip()
tips_text="> ".join(("\n"+tips_text.lstrip()).splitlines(True))
out_tips="## Tips:\n"+tips_text+"\n"

output=[out_title, out_ingredients, out_method, out_tips]
formatted_output="\n".join(output)

numlines = formatted_output.count('\n')
numimages = len(images)
image_spacing=ceil(numlines / numimages)
lines=formatted_output.splitlines()
if images:
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

shutil.copytree("submissions/"+friendly_title , "recipes/"+friendly_title ,ignore=shutil.ignore_patterns("*.raw"))