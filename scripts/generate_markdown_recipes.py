#builds recipes/<name>.md from each recipes/<name>/<name>.recipe stub (and the template)
#{photo.jpg} placeholders become images, and the site logo, tag badges and dates are added at the end
import html
from pathlib import Path
from common import badges, git_dates, humanize, recipe_tags

stubs = [Path('template/template/template.recipe')] + sorted(Path('recipes').glob('*/*.recipe'))
for stub in stubs:
    lines = stub.read_text(encoding='utf-8').splitlines()
    title_idx = next((i for i, l in enumerate(lines) if l.startswith('# ')), None)
    title = lines[title_idx][2:].strip() if title_idx is not None else stub.stem
    #title must be the first line for jekyll-titles-from-headings to name the page
    main_idx = next((i for i, l in enumerate(lines) if l.strip() == '{main.jpg}'), None)
    if main_idx is not None and title_idx is not None and main_idx < title_idx:
        lines.pop(main_idx)
        lines[title_idx:title_idx] = ['', '{main.jpg}']
    body = '\n'.join(lines).lstrip('\n')

    for image in sorted((stub.parent / 'images').glob('*.jpg')):
        main = image.name == 'main.jpg'
        alt = title if main else title + ' - photo ' + image.stem
        body = body.replace('{' + image.name + '}', '<img src="%s/images/%s" alt="%s" width="%s" align="right" />'
                            % (stub.parent.name, image.name, html.escape(alt), '55%' if main else '35%'))

    updated, created = git_dates(stub)
    #class lets the website's recipe layout restyle it (github and the pdf ignore it)
    dates = ('<p class="recipe-dates"><em>Created: %s &middot; Last updated: %s</em></p>' % (humanize(created), humanize(updated)))
    body += '\n\n<img src="../images/logo_sm.png" alt="gitFOOD logo" width="40%" />\n\n' + badges(recipe_tags(stub.parent)) + ' \n\n' + dates

    output = stub.parent.parent / (stub.stem + '.md')
    if not output.exists() or output.read_text(encoding='utf-8') != body:
        print('updating ' + str(output))
        output.write_text(body, encoding='utf-8', newline='\n')
