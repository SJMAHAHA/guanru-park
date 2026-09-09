import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
scene=bpy.data.scenes['00 · 完整建筑 | DAY'];bpy.context.window.scene=scene
candidates=[o for o in scene.objects if 'Dining table top' in o.name and o.name.startswith('1F')]
t=min(candidates,key=lambda o:(o.location-Vector(((903-1068)/18.75,(622-534)/18.75,3.95))).length);col=t.users_collection[0]
if not bpy.data.objects.get('1F | V3 dining linear pendant'):
 def box(name,offset,size,mat):
  bpy.ops.mesh.primitive_cube_add(size=1,location=t.location+Vector(offset));o=bpy.context.object;o.name=name;o.dimensions=size;o.rotation_euler.z=t.rotation_euler.z;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);o.data.materials.append(bpy.data.materials[mat]);o['room']='餐厅';mod=o.modifiers.new('Soft edges','BEVEL');mod.width=.006;mod.segments=3
  return o
 bar=box('1F | V3 dining linear pendant',(0,0,1.40),(1.8,.065,.065),'Charcoal metal')
 box('1F | V3 dining pendant diffuser',(0,0,1.366),(1.74,.050,.009),'Light warm')
 box('1F | V3 dining ceiling canopy',(0,0,2.02),(.70,.10,.045),'Charcoal metal')
 for dx in [-.6,.6]:
  box('1F | V3 dining suspension',(dx*math.cos(t.rotation_euler.z),dx*math.sin(t.rotation_euler.z),1.7),(.006,.006,.58),'Charcoal metal')
 d=bpy.data.lights.new('V3 dining task light','AREA');d.energy=55;d.shape='RECTANGLE';d.size=1.7;d.size_y=.09;d.color=(1,.83,.65);ob=bpy.data.objects.new(d.name,d);scene.collection.objects.link(ob);bpy.data.scenes['20 · 完整建筑 | TWILIGHT'].collection.objects.link(ob);ob.location=bar.location+Vector((0,0,-.04))
 fixtures=json.loads((ROOT/'web_export/lights.json').read_text());fixtures=[f for f in fixtures if f.get('kind')!='dining-pendant'];fixtures.append({'floor':'1F','room':'餐厅','kind':'dining-pendant','position':[ob.location.x,ob.location.z,-ob.location.y],'power':55,'range':5});(ROOT/'web_export/lights.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2))
cam=next(o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith('15 ·'));cam.location=Vector(((800-1068)/18.75,(622-813)/18.75,4.8));cam.rotation_euler=(Vector(((721-1068)/18.75,(622-785)/18.75,4.4))-cam.location).to_track_quat('-Z','Y').to_euler()
if __name__=='__main__':bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Guanru_Park_3.0.blend'))
