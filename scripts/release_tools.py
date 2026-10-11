#release helpers for the recipe book pipeline, run from the repo root with git and gh available
#  precheck BUMP                 is a build and comparison worth doing, prints key=value lines
#  next-version BUMP CHANGED     which version to release (and whether), CHANGED is true or false
#  notes [PREVIOUS]             release notes since the last release, plus those of today's releases it replaces
#  title VERSION [PREVIOUS]      release title, naming new recipes or a new layout, and today's earlier highlights
#  today                         today's releases, which the new release replaces
import json, re, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

#paths that can change the book's pages, so a build and comparison is worth doing
BOOK_INPUTS = ('recipes/', 'pdf/', 'images/', 'assets/fonts/', 'scripts/generate_pdfs.py', 'scripts/units.py', 'scripts/common.py', 'tags/groups.txt')
#files that change how every page looks, a minor release instead of a patch
STYLESHEET = 'pdf/book.css'
STYLE_FILES = ('assets/fonts/nunito-regular.ttf', 'assets/fonts/nunito-extrabold.ttf', 'images/logo_sm.png', 'images/logo_md.png')
#only the newest release of each day is kept, days in this timezone
TIMEZONE = 'Australia/Sydney'

def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def git(*args):
    return run('git', *args).stdout

def is_released(tag):
    return run('gh', 'release', 'view', tag).returncode == 0

def latest_release():
    return run('gh', 'release', 'view', '--json', 'tagName', '--jq', '.tagName').stdout.strip()

def changed_since(prev):
    return git('diff', '--name-only', f'{prev}..HEAD').split() if prev else []

def style_changed(prev, new='HEAD'):
    #the stylesheet counts only when its content changes, not its comments
    def sheet(rev):
        text = run('git', 'show', f'{rev}:{STYLESHEET}').stdout
        return re.sub(r'\s+', ' ', re.sub(r'/\*.*?\*/', '', text, flags=re.S)).strip()
    changed = git('diff', '--name-only', f'{prev}..{new}').split()
    return any(f in changed for f in STYLE_FILES) or sheet(prev) != sheet(new)

def current_version():
    return Path('version.txt').read_text().strip()

def precheck(bump):
    current, prev = current_version(), latest_release()
    unreleased = not is_released(current)
    if bump == 'none':
        build = False
    elif unreleased or bump in ('patch', 'minor') or not prev:
        build = True
    else:
        build = any(f.startswith(BOOK_INPUTS) for f in changed_since(prev))
    print(f'build={str(build).lower()}')
    print(f'prev={prev}')
    print(f'current={current}')
    print(f'unreleased={str(unreleased).lower()}')

def next_version(bump, pages_changed):
    current, prev = current_version(), latest_release()
    if not is_released(current):
        #set by hand, or an earlier release build failed, so release it as it is
        print(f'release=true\nversion={current}\nreason=unreleased version')
        return
    kind = bump
    if bump == 'auto':
        #a style change (colours, fonts, logos) leaves the text in place, so it counts on its own
        styled = bool(prev) and style_changed(prev)
        if not pages_changed and not styled and prev:
            print('release=false\nreason=the book pages are unchanged')
            return
        kind = 'minor' if styled else 'patch'
    major, minor, patch = (int(x) for x in current.split('.'))
    if kind == 'minor':
        minor, patch = minor + 1, 0
    else:
        patch += 1
    print(f'release=true\nversion={major}.{minor}.{patch}\nreason={kind} bump')

def slug_of(path):
    #recipes/name.md or recipes/name/anything gives name, other files in recipes/ are not recipes
    rest = path.split('/', 1)[1] if path.startswith('recipes/') else ''
    if not rest or ('/' not in rest and not rest.endswith('.md')):
        return None
    return rest.split('/')[0].removesuffix('.md')

def slugs_at(rev):
    return {s for s in (slug_of(p) for p in git('ls-tree', '-r', '--name-only', rev, 'recipes').split()) if s}

def title_of(slug, rev):
    for path in (f'recipes/{slug}/{slug}.recipe', f'recipes/{slug}.md'):
        text = run('git', 'show', f'{rev}:{path}').stdout
        match = re.search(r'^# (.+)$', text, re.M)
        if match:
            return match.group(1).strip()
    return slug

def listing(names, cap=12):
    #long lists are cut so a sweep over every recipe stays readable
    return ', '.join(names) if len(names) <= cap else f"{', '.join(names[:cap])} and {len(names) - cap} more"

def notes(prev, new='HEAD'):
    before, after = slugs_at(prev), slugs_at(new)
    kinds = {}
    for line in git('diff', '--name-only', '--no-renames', f'{prev}..{new}', '--', 'recipes').splitlines():
        slug = slug_of(line)
        if not slug or slug not in before & after:
            continue
        has_stub = bool(run('git', 'cat-file', '-e', f'{new}:recipes/{slug}/{slug}.recipe').returncode == 0)
        if line.endswith('.recipe') or (line.endswith('.md') and '/' not in line[len('recipes/'):] and not has_stub):
            kinds.setdefault(slug, set()).add('recipe')
        elif line.endswith('/tags.txt'):
            kinds.setdefault(slug, set()).add('tags')
        elif '/images/' in line:
            kinds.setdefault(slug, set()).add('photos')
    added = sorted(title_of(s, new) for s in after - before)
    removed = sorted(title_of(s, prev) for s in before - after)
    text = sorted(title_of(s, new) for s in kinds if kinds[s] & {'recipe', 'photos'})
    tags = sorted(title_of(s, new) for s in kinds if kinds[s] == {'tags'})
    lines = []
    for label, names in (('New recipes', added), ('Updated recipes', text), ('Tags updated', tags), ('Removed recipes', removed)):
        if names:
            lines.append(f'**{label} ({len(names)}):** {listing(names)}')
    if style_changed(prev, new):
        lines.append('**Book layout:** page layout, fonts or logos updated')
    if not lines:
        lines.append('No recipe or layout changes.')
    return f'### Changes since {prev}\n\n' + '  \n'.join(lines)

def released_today():
    #tags of the releases published today, newest first
    zone = ZoneInfo(TIMEZONE)
    day = lambda iso: datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(zone).date()
    rows = json.loads(run('gh', 'release', 'list', '--limit', '200', '--json', 'tagName,publishedAt').stdout or '[]')
    return [r['tagName'] for r in rows if day(r['publishedAt']) == datetime.now(zone).date()]

def release_field(tag, field):
    return run('gh', 'release', 'view', tag, '--json', field, '--jq', '.' + field).stdout.strip()

def day_notes(prev=''):
    #the new changes first, then the notes of today's releases, without their build lines
    parts = [notes(prev) if prev else 'First release.']
    parts += [re.sub(r'^Built automatically from .*$', '', release_field(tag, 'body'), flags=re.M).strip() for tag in released_today()]
    return '\n\n'.join(parts)

def title(version, prev=''):
    #the plain title unless recipes were added or the page style changed, plus today's earlier highlights
    added = sorted(title_of(s, 'HEAD') for s in slugs_at('HEAD') - slugs_at(prev)) if prev else []
    news = ['new book layout'] if prev and style_changed(prev) else []
    if added:
        news.append(f'new recipe: {added[0]}' if len(added) == 1 else f'{len(added)} new recipes')
    news += [m[1] for m in (re.search(r'\((.+)\)$', release_field(tag, 'name')) for tag in released_today()) if m]
    news = list(dict.fromkeys(news))
    #the generic layout note only when nothing more specific is named
    if len(news) > 1 and 'new book layout' in news:
        news.remove('new book layout')
    return f'v{version} - gitFOOD Recipe Book' + (' (' + ', '.join(news) + ')' if news else '')

if __name__ == '__main__':
    command, args = sys.argv[1], sys.argv[2:]
    if command == 'precheck':
        precheck(args[0])
    elif command == 'next-version':
        next_version(args[0], args[1] == 'true')
    elif command == 'notes':
        print(day_notes(*args))
    elif command == 'title':
        print(title(*args))
    elif command == 'today':
        print(' '.join(released_today()))
