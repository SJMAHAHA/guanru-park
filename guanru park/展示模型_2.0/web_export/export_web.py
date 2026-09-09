import bpy,os,json
from collections import defaultdict
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.context.window.scene=bpy.data.scenes['00 · 完整建筑 | DAY']
scene=bpy.context.scene
src=list(scene.objects)
# Work only in a temporary export scene; never save over the editable source.
export_scene=bpy.data.scenes.new('WEB_EXPORT')
bpy.context.window.scene=export_scene
for m in bpy.data.materials:
 if not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if p:
  if m.name=='Clear glazing':
   p.inputs['Transmission Weight'].default_value=0
   p.inputs['Alpha'].default_value=.23
   p.inputs['Base Color'].default_value=(.58,.78,.8,1)
   m.surface_render_method='DITHERED'
  if m.name=='Glassware':
   p.inputs['Transmission Weight'].default_value=0
   p.inputs['Alpha'].default_value=.28
   m.surface_render_method='DITHERED'
  if m.name=='Water':
   p.inputs['Transmission Weight'].default_value=0
   p.inputs['Base Color'].default_value=(.15,.5,.53,1)
   p.inputs['Roughness'].default_value=.22
# Evaluated mesh copies bake bevels and keep per-corner normals; merge by floor/category.
bpy.context.window.scene=scene
for lc in bpy.context.view_layer.layer_collection.children:
 if not lc.name.startswith('References'):lc.exclude=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
groups=defaultdict(list)
for o in src:
 if o.type not in {'MESH','CURVE'} or o.hide_render:continue
 cols=[c.name for c in o.users_collection]
 if any('Labels' in c or 'References' in c for c in cols):continue
 name=next((c for c in cols if ' / ' in c),None)
 if name:floor,cat=name.split(' / ',1)
 elif any(c.startswith('Site') for c in cols):floor,cat='Site','Landscape'
 else:continue
 # Ground is recreated as a lightweight infinite studio floor in the viewer.
 if 'Quiet presentation ground' in o.name:continue
 mesh=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
 cp=bpy.data.objects.new(o.name,mesh);cp.matrix_world=o.matrix_world.copy();export_scene.collection.objects.link(cp);groups[(floor,cat)].append(cp)
bpy.context.window.scene=export_scene
out=[]
for (floor,cat),objs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]
 bpy.ops.object.join()
 o=bpy.context.object;o.name=f'{floor}__{cat}';o['floor']=floor;o['category']=cat;o['version']='2.0'
 out.append({'name':o.name,'floor':floor,'category':cat,'faces':len(o.data.polygons),'vertices':len(o.data.vertices)})
bpy.ops.export_scene.gltf(filepath=str(OUT/'villa.glb'),export_format='GLB',use_active_scene=True,use_selection=False,export_apply=False,export_extras=True,export_cameras=False,export_lights=False,export_animations=False,export_texcoords=True,export_normals=True,export_yup=True)
(OUT/'manifest.json').write_text(json.dumps(out,indent=2))
print('WEB_EXPORT',len(out),'groups',sum(v['faces'] for v in out),'faces',os.path.getsize(OUT/'villa.glb'),'bytes')
