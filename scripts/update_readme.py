#writes README.md (recipe table for github), index.md (the site's recipe browser) and _data/recipes.json
import datetime, html, json, re
from pathlib import Path
from common import badges, git_dates, humanize, years, recipe_tags, tag_groups

TOC = []
for fpath in Path('recipes').glob('*.md'):
    text = fpath.read_text(encoding='utf-8')
    title = re.search(r'^# (.+)$', text, re.M)
    if not title:
        continue
    d = {'fpath': fpath, 'slug': fpath.stem, 'title': title[1].strip(), 'text': text,
         'tags': recipe_tags(Path('recipes', fpath.stem))}
    d['last_updated'], d['created'] = git_dates(Path('recipes', fpath.stem, fpath.stem + '.recipe'))
    TOC.append(d)
TOC.sort(key=lambda d: d['title'])
header= "|Recipe Title|Tags|Created|Last Updated|\n|:---|:---|:---|:---|\n"
recs = [f"|[{d['title']}]({ (Path('.')/d['fpath']).as_posix() })|{badges(d['tags'])}|{d['created']}|{d['last_updated']}|" for d in TOC]
toc_str= header + '\n'.join(recs)

readme = Path('README.stub').read_text(encoding='utf-8')
readme = readme.replace('{TOC}', toc_str)
Path('README.md').write_text(readme.replace('{years}', years(datetime.date.today().year)).strip(), encoding='utf-8', newline='\n')

#below is for the website, README.md above keeps image badges (github strips inline styles)
#tag grouping, colours and hidden tags come from tags/groups.txt

GROUPS, HIDDEN = tag_groups()
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
    #a tag links to the homepage filtered by it, recipes.js applies it in place
    group = 'meal' if tag == 'other' else group_of.get(tag, 'other')
    return f'<a class="tag t-{group}" href="./?tag={tag}">{tag.replace("_", " ")}</a>'

for d in TOC:
    serves = re.search(r'\*\*Serves:\*\*\s*([^\n<]+)', d['text'])
    d['serves'] = serves.group(1).strip() if serves else ''
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

#data for the recipe page layout (_layouts/recipe.html)
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
Path('_data/recipes.json').write_text(json.dumps(recipe_data, indent=1, sort_keys=True), encoding='utf-8', newline='\n')

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

index = Path('index.stub').read_text(encoding='utf-8').replace('{TOC}', recipe_browser(TOC))
Path('index.md').write_text(index, encoding='utf-8', newline='\n')
