from pathlib import Path
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
    return  f"{r():x}{r():x}{r():x}"

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
recs = [f"|[{d['title']}]({ Path('.')/d['fpath'] })|{make_badges(d['tags'])}|{d['created']}|{d['last_updated']}|" for d in TOC]
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
       
# overriding it this way is ugly but whatever
tag_badges_map = {tag_name:make_badge(label=tag_name, color = get_tag_hex_colour(tag_name), root='..') for tag_name in unq_tags}
def make_badges(unq_tags, sep=' '):
    return sep.join([tag_badges_map[tag] for tag in unq_tags])
   
Path("tags").mkdir(exist_ok=True)
for tag, pages in unq_tags.items():
    pages = sorted(pages, key=lambda x:x['title'])
    recs = [f"|[{d['title']}]({ Path('..')/d['fpath'] })|{make_badges(d['tags'])}|{d['created']}|{d['last_updated']}|" for d in pages]
    with open(f"tags/{tag}.md", 'w') as f:
        page_str = f"# {tag.replace('_'," ").title()} Recipes \n\n"
        page_str += header + '\n'.join(recs)
        f.write(page_str)
