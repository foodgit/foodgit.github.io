#helpers shared by the build scripts
import subprocess
from pathlib import Path

SITE_URL = 'https://foodgit.github.io/'
FIRST_YEAR = 2023  #first commit

def git_dates(path):
    """(last updated, created) iso dates from the file's git history, blank if untracked"""
    dates = subprocess.run(['git', 'log', '--format=%as', '--', str(path)], capture_output=True, text=True).stdout.split()
    return (dates[0], dates[-1]) if dates else ('', '')

def humanize(iso):
    """2023-06-25 as 25th of June 2023"""
    if not iso:
        return ''
    y, m, d = (int(x) for x in iso.split('-'))
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December']
    suffix = 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')
    return f'{d}{suffix} of {months[m - 1]} {y}'

def years(this_year):
    return str(FIRST_YEAR) if this_year == FIRST_YEAR else f'{FIRST_YEAR}–{this_year}'

def recipe_tags(folder):
    """the tags in a recipe folder's tags.txt, sorted"""
    path = Path(folder, 'tags.txt')
    return sorted(path.read_text(encoding='utf-8').split()) if path.exists() else []

def tag_groups():
    """tags/groups.txt as ({group: [tags]}, hidden tags)"""
    groups, hidden = {}, set()
    for line in Path('tags/groups.txt').read_text(encoding='utf-8').splitlines():
        line = line.split('#')[0].strip()
        if ':' in line:
            name, tags = (s.strip() for s in line.split(':', 1))
            if name == 'hidden':
                hidden.update(tags.split())
            else:
                groups[name] = tags.split()
    return groups, hidden
