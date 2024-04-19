from pathlib import Path
import random
import re
import subprocess
import time
import datetime
import os
from collections import defaultdict
from loguru import logger

random.seed(0)

def get_last_modified_date(fpath, verbose=True, timestamp=False):
    fmt = "%as"
    if timestamp:
        fmt="%at"
    # cmd = f"git log --pretty=format:{fmt}__%ae --".split()
    # cmd += [str(fpath)]
    # if verbose:
    #     logger.debug(cmd)
    # response = subprocess.run(cmd, capture_output=True)
    # commits = response.stdout.decode()
    # logger.debug(response)
    # commits = commits.split()
    # for c in commits:
    #     outv, author_email = c.split('__')
    #     if author_email != 'action@github.com':
    #         break
    # if verbose:
    #     try:
    #         logger.debug(outv)
    #     except:
    #         pass
    # try:
    #     return outv
    # except:
    #     return "N/A"

    t = os.path.getmtime(fpath)
    if timestamp:
        outv=datetime.datetime.fromtimestamp(t)
  
    else:
        outv=time.strftime('%Y-%m-%d', time.gmtime(t))
    #print(outv)
    return outv

def badges2kv(text):
    testpat = r'\/([a-zA-Z_]+-[a-zA-Z]+).svg'
    badges = re.findall(testpat, text)
    return [("tag", b.split('-')[0].split('.')[0]) for b in badges]

def make_badge(label, prefix='tag', color='lightgrey'):
    return f"[![](https://img.shields.io/badge/{prefix}-{label}-{color})](tags/{label}.md)"

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
                d_['last_modified'] = get_last_modified_date(fpath)
                d_['last_modified_ts'] = get_last_modified_date(fpath, timestamp=True)
                #d_['last_modified']=time.strftime('%Y-%m-%d', time.gmtime(int(d_['last_modified_ts'])))
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

header= "|Recipe Title|Tags\n|:---|:---|\n"
recs = [f"|[{d['title']}]({ Path('.')/d['fpath'] })|{make_badges(d['tags'])}|" for d in TOC]
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
tag_badges_map = {tag_name:make_badge(label=tag_name, color = get_tag_hex_colour(tag_name)) for tag_name in unq_tags}
def make_badges(unq_tags, sep=' '):
    return sep.join([tag_badges_map[tag] for tag in unq_tags])
   
Path("tags").mkdir(exist_ok=True)
for tag, pages in unq_tags.items():
    pages = sorted(pages, key=lambda x:x['title'])
    recs = [f"|[{d['title']}]({ Path('..')/d['fpath'] })|{make_badges(d['tags'])}|" for d in pages]
    with open(f"tags/{tag}.md", 'w') as f:
        page_str = f"# Pages tagged `{tag}`\n\n"
        page_str += header + '\n'.join(recs)
        f.write(page_str)
