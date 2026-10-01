from pathlib import Path
import datetime
import html
import json
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

SITE_URL = 'https://foodgit.github.io/'
FIRST_YEAR = 2023  # first commit
THIS_YEAR = datetime.date.today().year
COPYRIGHT_YEARS = str(FIRST_YEAR) if THIS_YEAR == FIRST_YEAR else f'{FIRST_YEAR}–{THIS_YEAR}'

def make_badge(label, prefix='tag', color='lightgrey'):
    # links to the site's homepage filtered by the tag (works from GitHub too)
    return f'<a href="{SITE_URL}?tag={label}"><img src="https://img.shields.io/badge/{prefix}-{label}-{color}" alt="{label}" /></a>'

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
                d_['text'] = text
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
    readme = readme.replace('{years}', COPYRIGHT_YEARS)
    readme = readme.strip()
if not readme:
    with open('empty.stub') as f:
        readme = f.read()

with open('README.md','w') as f:
    f.write(readme)
       
# Everything below is for the website. README.md (above) keeps image badges, since
# GitHub strips inline styles when showing it. The site's tag grouping, colours and
# hidden tags come from tags/groups.txt.

def load_groups(path='tags/groups.txt'):
    groups, hidden = {}, set()
    for line in open(path):
        line = line.split('#')[0].strip()
        if ':' not in line:
            continue
        name, tags = line.split(':', 1)
        if name.strip() == 'hidden':
            hidden.update(tags.split())
        else:
            groups[name.strip()] = tags.split()
    return groups, hidden

GROUPS, HIDDEN = load_groups()
group_of = {}
for g, tags in GROUPS.items():
    for t in tags:
        group_of.setdefault(t, g)
MEALS = GROUPS.get('meal', [])

def meals(d):
    return [t for t in d['tags'] if t in MEALS] or ['other']

def shown_tags(d):
    """meal tags first, then the rest in group order, without hidden tags"""
    order = {t: i for i, t in enumerate(t for tags in GROUPS.values() for t in tags)}
    rest = [t for t in d['tags'] if t not in HIDDEN and t not in MEALS]
    return meals(d) + sorted(rest, key=lambda t: order.get(t, len(order)))

def make_label(tag):
    # a tag links to the homepage filtered by it; recipes.js applies it in place
    group = 'meal' if tag == 'other' else group_of.get(tag, 'other')
    return f'<a class="tag t-{group}" href="./?tag={tag}">{tag.replace("_", " ")}</a>'

def suffix(day):
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 20, 'th')

def humanize(iso):
    if not iso:
        return ''
    y, m, d = (int(x) for x in iso.split('-'))
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December']
    return f'{d}{suffix(d)} of {months[m-1]} {y}'

for d in TOC:
    serves = re.search(r'\*\*Serves:\*\*\s*([^\n<]+)', d['text'])
    d['serves'] = serves.group(1).strip() if serves else ''
    d['slug'] = d['fpath'].stem
    d['meaningful'] = {t for t in d['tags'] if t not in HIDDEN}

def related(d, n=4):
    """recipes sharing the most meaningful tags (shared / combined)"""
    scored = []
    for o in TOC:
        if o is d or not d['meaningful'] or not o['meaningful']:
            continue
        score = len(d['meaningful'] & o['meaningful']) / len(d['meaningful'] | o['meaningful'])
        if score >= 0.25:
            scored.append((score, o['title'], o))
    return [o for _, _, o in sorted(scored, key=lambda s: (-s[0], s[1]))[:n]]

# data for the recipe page layout (_layouts/recipe.html)
Path('_data').mkdir(exist_ok=True)
recipe_data = {d['slug']: {
    'serves': d['serves'],
    'tags': [{'name': t, 'group': group_of.get(t, 'other')} for t in d['tags']],
    'facts': [{'name': t, 'group': group_of.get(t, 'other')} for t in shown_tags(d) if t != 'other'],
    'created': humanize(d['created']),
    'updated': humanize(d['last_updated']),
    'related': [{'title': o['title'], 'slug': o['slug'], 'meals': [m for m in meals(o) if m != 'other']}
                for o in related(d)],
} for d in TOC}
with open('_data/recipes.json', 'w') as f:
    json.dump(recipe_data, f, indent=1, sort_keys=True)

def recipe_browser(rows):
    """homepage: sidebar filters + recipe list, driven by assets/js/recipes.js"""
    ungrouped = sorted({t for d in rows for t in d['tags'] if t not in group_of and t not in HIDDEN})
    groups = list(GROUPS.items()) + ([('other tags', ungrouped)] if ungrouped else [])
    side = []
    for g, tags in groups:
        options = (tags + ['other']) if g == 'meal' else tags
        items = []
        for t in options:
            n = sum(t in (meals(d) if g == 'meal' else d['tags']) for d in rows)
            if n:
                items.append(f'<label><input type="checkbox" data-group="{g}" value="{t}"> '
                             f'{t.replace("_", " ")}<span class="count">{n}</span></label>')
        if items:
            side.append(f'<fieldset><legend>{g}</legend>{"".join(items)}</fieldset>')
    lis = []
    for d in rows:
        chips = ''.join(make_label(t) for t in shown_tags(d)[:6])
        lis.append(f'<li data-tags="{" ".join(d["tags"])}" data-meal="{" ".join(meals(d))}" '
                   f'data-created="{d["created"]}" data-updated="{d["last_updated"]}">'
                   f'<a class="recipe-name" href="./recipes/{d["slug"]}.html">{html.escape(d["title"])}</a>'
                   f'<div class="recipe-tags">{chips}</div></li>')
    return ('<div class="recipe-browser">'
            f'<aside class="filters">{"".join(side)}'
            '<button type="button" class="filters-done">Show recipes</button></aside>'
            '<div class="results"><div class="results-toolbar">'
            '<input type="search" class="recipe-search" placeholder="Search recipes" aria-label="Search recipes">'
            '<button type="button" class="filters-toggle">Filters</button>'
            '<select class="recipe-sort" aria-label="Sort recipes"><option value="name">A-Z</option>'
            '<option value="created">Newest</option><option value="updated">Recently updated</option></select></div>'
            '<div class="active-filters"></div><p class="results-status"></p>'
            f'<ul class="recipe-list">{"".join(lis)}</ul></div></div>')

with open('index.stub') as f:
    index_stub = f.read()
with open('index.md', 'w') as f:
    f.write(index_stub.replace('{TOC}', recipe_browser(TOC)))
