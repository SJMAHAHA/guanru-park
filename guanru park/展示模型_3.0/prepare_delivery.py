import json,html,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent;WEB=ROOT.parent.parent/'guanru-park-web'
# Each gallery image is a genuine V3 render.
for p in (ROOT/'renders').glob('*.png'):
 if '_Plan' in p.stem:continue
 im=Image.open(p).convert('RGB');im.thumbnail((2000,1600),Image.Resampling.LANCZOS);im.save(WEB/'public/gallery'/(p.stem+'.jpg'),quality=91,optimize=True)
 thumb=im.copy();thumb.thumbnail((360,260),Image.Resampling.LANCZOS);thumb.save(WEB/'public/gallery'/('thumb-'+p.stem+'.jpg'),quality=83,optimize=True)
 if p.stem=='01_Aerial':im.save(WEB/'public/preview-v3.jpg',quality=87,optimize=True)
items=[('aerial','整体鸟瞰'),('living','主客厅'),('kitchen','西厨'),('master','主卧'),('section','1F 楼层剖切')]
body=''
for key,title in items:
 body+=f'<section><h2>{title}</h2><div class="pair"><figure><figcaption>2.0 · 实际浏览器</figcaption><img src="v2-browser-{key}.jpg"></figure><figure><figcaption>3.0 · 实际浏览器 · 高画质</figcaption><img src="v3-browser-{key}.png"></figure></div></section>'
(ROOT/'qa/浏览器对比.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>Guanru Park 2.0 / 3.0 浏览器对比</title><style>body{font:16px system-ui;background:#edf1f0;color:#193239;margin:30px}h1{font-size:26px}section{margin:35px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:15px}figure{margin:0}img{width:100%;display:block}figcaption{padding:10px;background:white}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style><h1>Guanru Park · 2.0 / 3.0</h1><p>相同预设机位、1440 × 1000 视口。以下均为实际网页截图，未经画面替换；界面和近景入口随版本更新。</p>'+body+'</html>')
print('gallery renders converted',len(list((ROOT/'renders').glob('*.png'))))
