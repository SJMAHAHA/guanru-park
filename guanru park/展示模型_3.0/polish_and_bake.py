"""Finalize mounted equipment and bake reusable indirect irradiance on floor UV atlases."""
import bpy,json,math,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
scene=bpy.data.scenes['00 · 完整建筑 | DAY'];bpy.context.window.scene=scene
levels={'B1':0,'1F':3.15,'2F':6.3,'3F':9.45}
rooms=json.loads((ROOT/'room_schedule.json').read_text())
def floor(o):return next((c.name.split(' / ')[0] for c in o.users_collection if ' / ' in c.name),None)
def local_dims(o):return Vector(tuple(max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in range(3)))
# TV panels need actual wall mounting, not unsupported free-floating panels.
for o in list(scene.objects):
 if 'V3 display floor stand' in o.name or 'V3 display stand foot' in o.name or 'Flush ceiling downlight' in o.name:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
mounts=[]
# Resolve each display to a real supporting wall.
for o in [o for o in scene.objects if o.type=='MESH' and 'TV / display' in o.name]:
 f=floor(o);candidates=[w for w in scene.objects if w.type=='MESH' and floor(w)==f and any(t in w.name for t in ['Partition','Opaque facade']) and local_dims(w).x>1.95 and w.dimensions.z>2]
 if not candidates:continue
 w=min(candidates,key=lambda w:(Vector((w.location.x,w.location.y,0))-Vector((o.location.x,o.location.y,0))).length);dims=local_dims(w);sign=1 if (w.matrix_world.inverted()@o.location).y>0 else -1
 o.location=w.matrix_world@Vector((0,sign*(dims.y/2+.065),0));o.location.z=levels[f]+1.5;o.rotation_euler=w.rotation_euler;o['mount']='wall bracket';o['wall']=w.name
 mounts.append({'display':o.name,'wall':w.name})
 # Mounting bracket, editable and supported by the wall.
 mesh=bpy.data.meshes.new('Display bracket');vs=[(x,y,z) for x in [-.18,.18] for y in [-.04,.04] for z in [-.14,.14]];mesh.from_pydata(vs,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);mesh.materials.append(bpy.data.materials['Charcoal metal']);br=bpy.data.objects.new(f+' | V3 display wall bracket',mesh);o.users_collection[0].objects.link(br);br.location=w.matrix_world@Vector((0,sign*(dims.y/2+.025),0));br.location.z=o.location.z;br.rotation_euler=o.rotation_euler
# Align the recessed trim to the finished ceiling; the lens sits just below it.
for o in list(scene.objects):
 if o.name.startswith('V3 ') and any(k in o.name for k in ['recessed downlight trim','downlight lens',' downlight']):o.location.z+=.039
fixtures=json.loads((ROOT/'web_export/lights.json').read_text())
for d in fixtures:d['position'][1]+=.039
(ROOT/'web_export/lights.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2))
# All new downlights are also available in the evening scene.
evening=bpy.data.scenes['20 · 完整建筑 | TWILIGHT'];newlights=bpy.data.collections.new('Lighting · V3 room fixtures');evening.collection.children.link(newlights)
for o in list(scene.objects):
 if o.type=='LIGHT' and o.name.startswith('V3 '):newlights.objects.link(o)
# New primary bathroom and full kitchen-detail views supplement the original comparison cameras.
camcol=bpy.data.collections['Cameras · 展示视角']
def P(x,y,z):return Vector(((x-1068)/18.75,(622-y)/18.75,z))
for name,loc,target in [('13 · 主卫室内',P(777,700,7.9),P(737,610,7.35)),('14 · 西厨设备近景',P(831,535,4.8),P(799,449,4.50)),('15 · 中厨室内',P(800,813,4.8),P(716,785,4.4))]:
 d=bpy.data.cameras.new(name);d.lens=24;ob=bpy.data.objects.new(name,d);camcol.objects.link(ob);ob.location=loc;ob.rotation_euler=(target-loc).to_track_quat('-Z','Y').to_euler()
exec(compile((ROOT/'repair_bath_mounts.py').read_text(),str(ROOT/'repair_bath_mounts.py'),'exec'),dict(globals(),__name__='bath_repair'))
exec(compile((ROOT/'final_fixtures.py').read_text(),str(ROOT/'final_fixtures.py'),'exec'),dict(globals(),__name__='fixture_final'))
# UV2 atlas on the actual floor meshes, preserving holes and original tiled/wood UVs.
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
 for d in pref.devices:d.use=d.type=='METAL'
 scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
for lc in bpy.context.view_layer.layer_collection.children:
 if not lc.name.startswith('References'):lc.exclude=False
out=ROOT/'web_export/lightmaps';out.mkdir(exist_ok=True)
report=[]
for f in levels:
 targets=[o for o in scene.objects if o.type=='MESH' and floor(o)==f and ('floor finish' in o.name or 'Roof pavilion finish' in o.name)]
 if not targets:continue
 col=bpy.data.collections.new(f+' / BakedFloors');bpy.data.collections[f+' · '+{'B1':'康体娱乐与车库','1F':'公共起居与平台','2F':'卧室与退台','3F':'屋顶平台与局部房间'}[f]].children.link(col)
 for o in targets:
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o)
  if o.data.users>1:o.data=o.data.copy()
 bpy.ops.object.select_all(action='DESELECT')
 for o in targets:o.select_set(True)
 bpy.context.view_layer.objects.active=targets[0];bpy.ops.object.join();o=bpy.context.object;o.name=f+' | V3 baked floor surfaces'
 # Copy materials, connect the portable color textures explicitly to UVMap.
 for i,m in enumerate(list(o.data.materials)):
  mm=m.copy();mm.name='V3 '+f+' floor '+m.name;o.data.materials[i]=mm
  uvnode=mm.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UVMap'
  for n in mm.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:mm.node_tree.links.new(uvnode.outputs['UV'],n.inputs['Vector'])
 uv=o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active=uv
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
 im=bpy.data.images.new('V3 '+f+' indirect irradiance',2048,2048,alpha=False,float_buffer=True);im.colorspace_settings.name='Linear Rec.709'
 for m in o.data.materials:
  n=m.node_tree.nodes.new('ShaderNodeTexImage');n.name='V3 baked indirect';n.image=im;m.node_tree.nodes.active=n
 scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=True;scene.render.bake.use_pass_color=False;scene.render.bake.margin=8
 started=time.time();bpy.ops.object.bake(type='DIFFUSE',uv_layer='LightmapUV')
 # HDR linear irradiance keeps highlights unclipped for browser LightMap use.
 im.filepath_raw=str(out/(f+'.hdr'));im.file_format='HDR';im.save();im.pack()
 # glTF exporter exports UVs referenced by nodes: a separate unused output group documents UV2.
 for m in o.data.materials:
  node=m.node_tree.nodes.get('V3 baked indirect');uvnode=m.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='LightmapUV';m.node_tree.links.new(uvnode.outputs['UV'],node.inputs['Vector'])
 o.data.uv_layers.active=o.data.uv_layers['UVMap'];o['lightmap']=f+'.hdr';o['lightmap_uv']='LightmapUV'
 report.append({'floor':f,'image':f+'.hdr','seconds':round(time.time()-started,2),'size':2048})
 print('V3 BAKE',report[-1],flush=True)
(ROOT/'qa/lightmap_bake.json').write_text(json.dumps(report,indent=2));(ROOT/'qa/display_mounts.json').write_text(json.dumps(mounts,indent=2))
scene['version']='3.0';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Guanru_Park_3.0.blend'))
print('V3 POLISH AND BAKE COMPLETE',flush=True)
