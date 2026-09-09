import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
scene=bpy.data.scenes['00 · 完整建筑 | DAY'];bpy.context.window.scene=scene;bpy.context.view_layer.update()
rooms=json.loads((ROOT/'room_schedule.json').read_text())
report={'objects':len(scene.objects),'rooms':[], 'forbidden_cabinets':[], 'nonfinite':[], 'images_missing':[]}
terms=['cabinet carcass','bedside cabinet','media console','sitting room console','bookcase','wardrobe','dressing island','bath vanity','wine rack backing']
for o in scene.objects:
 if any(not math.isfinite(v) for row in o.matrix_world for v in row):report['nonfinite'].append(o.name)
 if any(t in o.name.lower() for t in terms) and o.get('room') not in ['中厨','西厨']:report['forbidden_cabinets'].append(o.name)
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists():report['images_missing'].append(im.name)
for r in rooms:
 x1,y1,x2,y2=r['reference_rect'];z={'B1':0,'1F':3.15,'2F':6.3,'3F':9.45}[r['floor']]
 inside=[]
 for o in scene.objects:
  if o.type not in ['MESH','LIGHT','CURVE']:continue
  c=sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8 if o.type!='LIGHT' else o.location
  x=c.x*18.75+1068;y=622-c.y*18.75
  if x1<=x<=x2 and y1<=y<=y2 and z<=c.z<z+3.15:inside.append(o)
 row={'floor':r['floor'],'name':r['name'],'objects_in_room_bounds':len(inside),'real_lights':sum(o.type=='LIGHT' for o in inside),'furniture_parts':sum(any('/ Furniture' in c.name for c in o.users_collection) for o in inside),'ceiling_parts':sum('ceiling' in o.name.lower() for o in inside),'policy':r['cabinet_policy']}
 report['rooms'].append(row)
(ROOT/'qa/room-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()},ensure_ascii=False))
