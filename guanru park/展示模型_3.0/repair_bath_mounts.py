import bpy, math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parent
def P(x,y,z): return Vector(((x-1068)/18.75,(622-y)/18.75,z))
def frame(x,y,ang): return Matrix.Translation(P(x,y,6.335)) @ Matrix.Rotation(math.radians(ang),4,'Z')
old=frame(716,624,90)
wash=frame(772,534,270)@old.inverted()
shower=frame(772,714,270)@(old@Matrix.Translation(Vector((-3.2,0,0)))).inverted()
for o in bpy.data.objects:
 if o.get('room')!='主卫西区' or o.get('support_repaired'): continue
 n=o.name
 if any(t in n for t in ['basin','bathroom mirror','mirror light','mirror linear','bathroom towel','hand towel']):
  o.matrix_world=wash@o.matrix_world;o['support_repaired']='east partition 780 / 514–554'
 elif any(t in n for t in ['shower','rainfall']):
  o.matrix_world=shower@o.matrix_world;o['support_repaired']='east partition 780 / 696–734'
cam=next((o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith('13 ·')),None)
if cam:
 cam.location=P(715,600,7.92);cam.rotation_euler=(P(777,545,7.4)-cam.location).to_track_quat('-Z','Y').to_euler()
# Keep the thin mirror surface in front of the finished wall face.
for o in bpy.data.objects:
 if 'V3 bathroom mirror' in o.name and not o.get('mirror_surface_offset'):
  o.location+=o.rotation_euler.to_matrix()@Vector((0,-.08,0));o['mirror_surface_offset']=True
for o in bpy.data.objects:
 if any(k in o.name for k in ['V3 bathroom towel bar','V3 hand towel']) and not o.get('towel_clearance_repaired'):
  o.location.z-=.35;o['towel_clearance_repaired']=True
if __name__=='__main__':bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Guanru_Park_3.0.blend'))
