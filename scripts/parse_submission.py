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
issue_title = sys.argv[1]
issue_body = sys.argv[2]

print("Parsing issue with python script")
print("Issue title: "+issue_title)
recipe_title=issue_body.split("### ")[1].split("\n")[2]
friendly_title=recipe_title.strip().replace(" ","").lower()
print("Recipe title: "+recipe_title)
print("Friendly title: "+friendly_title)

output_file = Path("submissions/"+friendly_title+"/images/.placeholder")
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text("placeholder text")

output_file = Path("submissions/"+friendly_title+"/"+friendly_title+".raw")
output_file.parent.mkdir(exist_ok=True, parents=True)
output_file.write_text(issue_body)

recipe_file_name="submissions/"+friendly_title+"/"+friendly_title+".raw"

with open(recipe_file_name,'r') as f:
    body = f.read()
    f.close()

image_links=re.findall(r'!\[[^\]]*\]\((.*?)\s*?\s*\)', body)

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
        get_image(image)
# for image in images:
#     print("downloaded "+image["name"]) 
        