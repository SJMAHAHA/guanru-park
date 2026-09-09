import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
V1=ROOT.parent/'展示模型_20260907'/'Guanru_Park_展示模型.blend';V2=ROOT/'Guanru_Park_2.0.blend'
keys=['B1 foundation footprint','1F curved platform structural slab','2F H footprint with open south court','Broad H roof / 2F ceiling','Thin upper pavilion roof']
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.data.scenes['00 · 完整建筑 | DAY'];bpy.context.window.scene=sc;bpy.context.view_layer.update();result={}
 for key in keys:
  obj=next(o for o in sc.objects if key in o.name);verts=sorted(tuple(round(c,5) for c in obj.matrix_world@v.co) for v in obj.data.vertices);result[key]={'vertex_hash':hashlib.sha256(repr(verts).encode()).hexdigest(),'vertices':len(verts),'faces':len(obj.data.polygons)}
 return {'shapes':result,'objects':len(sc.objects),'scenes':len(bpy.data.scenes),'materials':len(bpy.data.materials),'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),'version':sc.get('version','1.0')}
a=snapshot(V1);b=snapshot(V2);assert a['shapes']==b['shapes'],'Core footprints or slab openings changed'
assert b['objects']>a['objects'];assert b['packed_images']>=24;assert b['scenes']==6
for prefix,count in [('V2 Draped duvet',13),('V2 folded linen curtain',4),('V2 Hollow washbasin',16)]:
 actual=sum(prefix.lower() in o.name.lower() for o in bpy.context.scene.objects);assert actual>=count,(prefix,actual)
rooms1=json.loads((V1.parent/'room_schedule.json').read_text());rooms2=json.loads((ROOT/'room_schedule.json').read_text());assert rooms1==rooms2
report={'source_v1_sha256':hashlib.sha256(V1.read_bytes()).hexdigest(),'source_v2_sha256':hashlib.sha256(V2.read_bytes()).hexdigest(),'v1':a,'v2':b,'core_shapes_and_openings_preserved':True,'room_schedule_preserved':True,'room_count':len(rooms2)}
(ROOT/'qa/version_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('V2 COMPARISON PASSED',json.dumps({'v1_objects':a['objects'],'v2_objects':b['objects'],'packed_images':b['packed_images'],'scenes':b['scenes']}),flush=True)
