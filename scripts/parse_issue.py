import sys
from pathlib import Path

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