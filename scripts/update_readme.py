from pathlib import Path
import html
import random
import re
import subprocess
from collections import defaultdict
#from loguru import logger

random.seed(0)

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

def badges2kv(text):
    testpat = r'\/([a-zA-Z_]+-[a-zA-Z]+).svg'
    badges = re.findall(testpat, text)
    return [("tag", b.split('-')[0].split('.')[0]) for b in badges]

def make_badge(label, prefix='tag', color='lightgrey', root='.'):
    # return f"[![{label}](https://img.shields.io/badge/{prefix}-{label}-{color})](tags/{label}.md){{:target=\"_blank\"}}"
    return f'<a href="{root}/tags/{label}.html"><img src="https://img.shields.io/badge/{prefix}-{label}-{color}" alt="{label}" /></a>'

def random_hex_colour():
    """generates a string for a random hex color"""
    r = lambda: random.randint(0,255)
    return  f"{r():02x}{r():02x}{r():02x}"

def get_tag_hex_colour(tag_name):
    tag_file = Path('./tags/colours/'+tag_name+'.hex')
    try:
        with open(tag_file) as f:
            tag_hex=f.readline()
    except:
        tag_hex=random_hex_colour()
        tag_file.parent.mkdir(exist_ok=True, parents=True)
        tag_file.write_text(tag_hex)
    return tag_hex

md_files = Path('./recipes').glob('*.md')
TOC = []
unq_tags = defaultdict(list)
for fpath in list(md_files):
    if fpath.name == 'README.md':
        continue
    with open(fpath) as f:
        for line in f:
             if line.startswith('# '):
                header=line
                text = f.read()
                badge_meta = badges2kv(text)
                d_ = {'fpath':fpath}
                d_['title'] = header[2:].strip()
                stub_path = Path('recipes')/fpath.stem/f"{fpath.stem}.recipe"
                d_['last_updated'], d_['created'] = get_dates(stub_path)
                d_['n_char'] = len(text)
                d_['tags'] = [v for k,v in badge_meta if k =='tag']
                d_['tags'].sort()
                #unq_tags.update(d_['tags'])
                for tag in d_['tags']:
                    unq_tags[tag].append(d_)
                TOC.append(d_)
                break

tag_badges_map = {tag_name:make_badge(label=tag_name, color = get_tag_hex_colour(tag_name)) for tag_name in unq_tags}

def make_badges(unq_tags, sep=' '):
    return sep.join([tag_badges_map[tag] for tag in unq_tags])
    
try:
    TOC = sorted(TOC, key=lambda x:x['title'])
except:
    pass

header= "|Recipe Title|Tags|Created|Last Updated|\n|:---|:---|:---|:---|\n"
recs = [f"|[{d['title']}]({ (Path('.')/d['fpath']).as_posix() })|{make_badges(d['tags'])}|{d['created']}|{d['last_updated']}|" for d in TOC]
toc_str= header + '\n'.join(recs)

readme = None
if Path('README.stub').exists():
    with open('README.stub') as f:
        readme_stub = f.read()
    readme = readme_stub.replace('{TOC}', toc_str)
    readme = readme.replace('{tags}', make_badges(unq_tags))
    readme = readme.strip()
if not readme:
    with open('empty.stub') as f:
        readme = f.read()

with open('README.md','w') as f:
    f.write(readme)
       
# The site's homepage (index.md) and tag pages use plain styled tag labels and an
# HTML table that assets/js/recipes.js makes sortable and filterable. README.md
# keeps image badges, since GitHub strips inline styles when showing it.

def label_colours(tag):
    # older colour files can have 5 hex digits (the generator didn't zero-pad)
    bg = get_tag_hex_colour(tag).strip().lstrip('#').rjust(6, '0')[:6]
    def linear(c):
        c /= 255
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
    r, g, b = (linear(int(bg[i:i+2], 16)) for i in (0, 2, 4))
    luminance = 0.2126*r + 0.7152*g + 0.0722*b
    return '#'+bg, ('#111' if luminance > 0.3 else '#fff')

def make_label(tag, root):
    bg, fg = label_colours(tag)
    return (f'<a class="tag" href="{root}/tags/{tag}.html" style="background:{bg};color:{fg}">'
            f'{tag.replace("_", " ")}</a>')

def recipe_table(rows, root):
    out = ['<table class="recipes">',
           '<thead><tr><th data-sort>Recipe</th><th>Tags</th>'
           '<th data-sort class="date">Created</th><th data-sort class="date">Last updated</th></tr></thead>',
           '<tbody>']
    for d in rows:
        href = root+'/'+d['fpath'].with_suffix('.html').as_posix()
        labels = ' '.join(make_label(t, root) for t in d['tags'])
        out.append(f'<tr><td><a href="{href}">{html.escape(d["title"])}</a></td><td class="tags">{labels}</td>'
                   f'<td class="date">{d["created"]}</td><td class="date">{d["last_updated"]}</td></tr>')
    out += ['</tbody>', '</table>']
    return '\n'.join(out)

with open('index.stub') as f:
    index_stub = f.read()
with open('index.md', 'w') as f:
    f.write(index_stub.replace('{TOC}', recipe_table(TOC, '.')))

Path("tags").mkdir(exist_ok=True)
for tag, pages in unq_tags.items():
    pages = sorted(pages, key=lambda x:x['title'])
    with open(f"tags/{tag}.md", 'w') as f:
        f.write(f"# {tag.replace('_'," ").title()} Recipes\n\n"+recipe_table(pages, '..')+'\n')
