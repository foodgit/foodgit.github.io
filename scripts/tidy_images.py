#keeps the recipe images tidy: no .gitkeep beside other files, photos no bigger than print needs
from pathlib import Path
from PIL import Image, ImageOps

#longest side in pixels: 300 dpi across the book's 180mm main photo, step photos are far smaller
LIMITS = {'main.jpg': 2126}
STEP_LIMIT = 1200

for keep in Path('recipes').glob('*/images/.gitkeep'):
    if any(p != keep for p in keep.parent.iterdir()):
        keep.unlink()

for path in Path('recipes').glob('*/images/*.jpg'):
    im = ImageOps.exif_transpose(Image.open(path))
    limit = LIMITS.get(path.name, STEP_LIMIT)
    if max(im.size) > limit:
        im.thumbnail((limit, limit), Image.LANCZOS)
        im.save(path, quality=90, optimize=True, icc_profile=im.info.get('icc_profile'))
        print('%s: %dx%d' % (path, *im.size))
