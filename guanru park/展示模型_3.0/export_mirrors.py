import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;out=[]
for o in bpy.data.scenes['00 · 完整建筑 | DAY'].objects:
 if 'V3 bathroom mirror' not in o.name:continue
 f=next((c.name.split(' / ')[0] for c in o.users_collection if ' / ' in c.name),None)
 if not f:continue
 normal=o.rotation_euler.to_matrix()@Vector((0,-1,0));pos=o.location+normal*.026
 size=[max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in [0,2]]
 out.append({'floor':f,'room':o.get('room'),'position':[pos.x,pos.z,-pos.y],'normal':[normal.x,normal.z,-normal.y],'size':size})
(ROOT/'web_export/mirrors.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('Exported mirror planes',len(out))
