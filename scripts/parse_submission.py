import re
import shutil
import sys
from pathlib import Path
import requests

def get_image(image):
    print("downloading "+image["name"])
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

print("Parsing issue with python script")
recipe_title=issue_body.split("### ")[1].split("\n")[2]
friendly_title=recipe_title.strip().replace(" ","").lower()
print("Recipe title: "+recipe_title)
print("Friendly title: "+friendly_title)

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
            "name":image_name,
            "location":"submissions/"+friendly_title+"/images/"+image_name,
            "url":image_link
        }
        images.append(image)
        #get_image(image)

with open(recipe_file_name,'r') as f:
    body_lines = f.readlines()
read_nextline=False
tags=[]
for line in body_lines:
    if line[:6]=="- [X] ":
        tag=line[6:].strip().lower()
        tags.append(tag)
        print(tag)

additional_tags=issue_body.split("### Additional tags")[1].split("\n")[2].lower().replace(", ",",").replace(" ","_").split(",")
with open("submissions/"+friendly_title+"/tags.txt", 'w') as f:
    f.write('\n'.join(map(str, tags+additional_tags)))
