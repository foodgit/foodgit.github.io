#turns a recipe submission issue (the submitrecipe.yml form) into recipes/<name>/ with a stub, tags and photos
#takes the issue body text, or a file containing it, the raw body is kept in submissions/<name>/
import re, shutil, sys, urllib.request
from math import ceil
from pathlib import Path

issue_body = sys.argv[1] if sys.argv[1].startswith('###') else Path(sys.argv[1]).read_text(encoding='utf-8')

def section(label):
    """the answer under a '### label' heading of the issue form ('' if left empty)"""
    parts = issue_body.split('### ' + label)
    if len(parts) < 2:
        return ''
    text = parts[1].split('### ')[0].strip()
    return '' if text == '_No response_' else text

def listed(text, marker):
    #one list item per non-blank line, blank lines between entries used to become empty items
    return '\n'.join(marker + line.strip() for line in text.splitlines() if line.strip())

recipe_title = section('Title of Recipe')
name = re.sub(r'[^a-z0-9]', '', recipe_title.lower())
folder = Path('submissions', name)
(folder / 'images').mkdir(parents=True, exist_ok=True)
(folder / 'images/.gitkeep').write_text('placeholder text')
(folder / (name + '.raw')).write_text(issue_body, encoding='utf-8')

#the first photo is the main one, the rest are numbered
images = []
for i, url in enumerate(re.findall(r'!\[[^\]]*\]\((.*?)\s*\)', issue_body)):
    image_name = 'main.jpg' if i == 0 else str(i) + '.jpg'
    print('downloading ' + url)
    urllib.request.urlretrieve(url, folder / 'images' / image_name)
    images.append('{' + image_name + '}')

#ticked boxes, additional tags and difficulty, as lowercase_with_underscores
tags = [line[6:] for line in issue_body.splitlines() if line[:6].lower() == '- [x] ']
tags += section('Additional tags').split(',') + [section('How difficult is it to prepare this meal?')]
tags = sorted({t.strip().lower().replace(' ', '_') for t in tags} - {''})
(folder / 'tags.txt').write_text('\n'.join(tags), encoding='utf-8')

tips, serves = section('Tips'), section('How many people does it serve?')
output = ['# ' + recipe_title + '\n',
          '## Ingredients\n\n' + listed(section('Ingredients'), '- ') + '\n',
          '## Method\n\n' + listed(section('Method'), '> 1. ') + '\n',
          '## Tips\n\n' + listed(tips, '> - ') + '\n' if tips else '',
          '**Serves:** ' + serves + '\n' if serves else '']
if images:
    output.insert(0, '\n')
lines = '\n'.join(output).splitlines()
#photos spread evenly down the recipe
for i, tag in enumerate(images):
    lines[min(i * ceil(len(lines) / len(images)), len(lines) - 1)] += ' ' + tag
(folder / (name + '.recipe')).write_text('\n'.join(lines), encoding='utf-8')
print('saved ' + str(folder))

shutil.rmtree(Path('recipes', name), ignore_errors=True)
shutil.copytree(folder, Path('recipes', name), ignore=shutil.ignore_patterns('*.raw'))
