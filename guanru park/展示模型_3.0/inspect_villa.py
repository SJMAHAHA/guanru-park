import bpy,os,json,math,sys
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__))
main=bpy.data.scenes['00 · 完整建筑 | DAY']
# Geometric sanity and major furniture/wall overlaps, to guide visual review.
report={'file_opened':bpy.data.filepath,'objects':len(main.objects),'missing_external_images':[],'nonfinite':[],'major_furniture_wall_overlaps':[]}
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):report['missing_external_images'].append(im.name)
for o in main.objects:
 if any(not math.isfinite(v) for row in o.matrix_world for v in row):report['nonfinite'].append(o.name)
def bounds(o):
 v=[o.matrix_world@Vector(p) for p in o.bound_box];return ([min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)])
wallnames=['Partition','Opaque facade','Square structural pier','Double glazing']
furnames=['Sofa upholstered base','Lounge chair upholstered base','Bed upholstered frame','Dining table top','Cabinet carcass','Office desk','Kitchen stone counter','Cinema projection wall','Treadmill base','Billiard table frame']
ws=[(o,bounds(o)) for o in main.objects if o.type=='MESH' and any(n in o.name for n in wallnames)]
for o in main.objects:
 if o.type!='MESH' or not any(n in o.name for n in furnames):continue
 a,b=bounds(o)
 for w,(c,d) in ws:
  overlap=[min(b[i],d[i])-max(a[i],c[i]) for i in range(3)]
  if min(overlap)>.015 and math.prod(overlap)>(.002 if 'Double glazing' in w.name else .012):
   report['major_furniture_wall_overlaps'].append({'furniture':o.name,'wall':w.name,'location':[round(v,3) for v in o.location],'overlap_m':[round(v,3) for v in overlap]})
with open(os.path.join(ROOT,'qa','validation.json'),'w') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print('VALIDATION',json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()}),flush=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if 'preview' in args:
 for lev in ['B1','1F','2F']:
  sc=bpy.data.scenes['10 · '+lev+' 家具平面 / isolated'];sc.render.resolution_percentage=50;sc.cycles.samples=12;sc.render.filepath=os.path.join(ROOT,'qa',lev+'_plan_preview.png');bpy.ops.render.render(write_still=True,scene=sc.name)
 for key in ['08 ·','09 ·']:
  main.camera=next(o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith(key));main.render.resolution_percentage=50;main.cycles.samples=16;main.render.filepath=os.path.join(ROOT,'qa',key[:2]+'_interior_preview.png');bpy.ops.render.render(write_still=True,scene=main.name)
