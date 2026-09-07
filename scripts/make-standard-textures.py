"""Generate 1K texture variants. Requires Pillow: python3 scripts/make-standard-textures.py."""
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent.parent/'public/assets-v3/textures'
(root/'standard').mkdir(parents=True,exist_ok=True)
for source in (root/'high').iterdir():
    image=Image.open(source)
    image.thumbnail((1024,1024),Image.Resampling.LANCZOS)
    image.save(root/'standard'/source.name,quality=88,optimize=True)
print('Generated standard texture tier')
