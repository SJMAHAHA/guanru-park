"""Render V2: Blender -b Guanru_Park_2.0.blend --python render_views.py -- [all|01..12] [preview]."""
import bpy,os,sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['all'];preview='preview' in args;selected=set(a for a in args if a not in ['all','preview'])
main=bpy.data.scenes['00 · 完整建筑 | DAY'];evening=bpy.data.scenes['20 · 完整建筑 | TWILIGHT']
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();gpus=[d for d in prefs.devices if d.type=='METAL'];assert gpus
 for d in prefs.devices:d.use=d.type=='METAL'
 for sc in bpy.data.scenes:sc.cycles.device='GPU'
except Exception as e:
 print('CPU rendering',e,flush=True)
 for sc in bpy.data.scenes:sc.cycles.device='CPU'
views=[('01','01_Aerial'),('02','02_East'),('03','03_Courtyard'),('04','04_Pool'),('08','08_Living'),('09','09_Master'),('10','10_Kitchen'),('11','11_Twilight')]
log=[]
def render(sc,key):
 sc.render.resolution_percentage=45 if preview else 100;sc.cycles.samples=24 if preview else 96;sc.cycles.use_denoising=True
 path=ROOT/('qa' if preview else 'renders')/(key+('_preview' if preview else '')+'.png');sc.render.filepath=str(path)
 t=time.time();bpy.ops.render.render(write_still=True,scene=sc.name);log.append({'file':str(path),'seconds':round(time.time()-t,2),'scene':sc.name});print('V2 RENDER',key,log[-1]['seconds'],flush=True)
for num,key in views:
 if selected and num not in selected:continue
 sc=evening if num=='11' else main;sc.camera=next(o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith(num+' ·'));render(sc,key)
for num,f in [('05','B1'),('06','1F'),('07','2F'),('12','3F')]:
 if selected and num not in selected:continue
 sc=bpy.data.scenes['10 · '+f+' 家具平面 / isolated']
 for typ,match in [('Plan','家具平面'),('Axon','剖切轴测')]:
  sc.camera=next(o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith(f+' ·') and match in o.name);render(sc,num+'_'+f+'_'+typ)
(ROOT/'qa'/('render_log_'+('_'.join(args))+'.json')).write_text(json.dumps(log,ensure_ascii=False,indent=2))
print('V2 RENDER FINISHED',len(log),flush=True)
