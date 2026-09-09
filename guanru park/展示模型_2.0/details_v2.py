"""V2 presentation detailing. Executed by build_villa.py before furnishing.
Original footprints, walls, room coordinates and slab openings stay authoritative.
"""
import bmesh
from pathlib import Path
V2_ADDED={}
_v1_sofa=sofa;_v1_chair=chair;_v1_armchair=armchair;_v1_bed=bed
_v1_kitchen=kitchen;_v1_bath=bath;_v1_cabinet=cabinet
_v1_cyl=cyl

def cyl(name,loc,r,depth,ma='Charcoal metal',vertices=48,col=None):
 o=_v1_cyl(name,loc,r,depth,ma,max(vertices,48),col)
 if depth>.025 and r>.05:
  q=o.modifiers.new('V2 rounded lathed edge','BEVEL');q.width=min(.009,depth*.12);q.segments=2
 return o

def CY(n,loc,r,h,ma='Charcoal metal'):return cyl(n,V(*loc),r,h,ma)

def tube(name,points,r=.008,ma='Brass',closed=False,col=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
 sp.use_cyclic_u=closed;o=bpy.data.objects.new(floorid+' | V2 '+name,cu);(col or CUR).objects.link(o);cu.materials.append(M[ma]);return o

def lathe(name,profile,loc=(0,0,0),ma='Porcelain',segments=48):
 verts=[];faces=[]
 for r,z in profile:
  for i in range(segments):a=i*2*pi/segments;verts.append(V(loc[0]+r*cos(a),loc[1]+r*sin(a),loc[2]+z))
 for j in range(len(profile)-1):
  for i in range(segments):k=j*segments+i;kn=j*segments+(i+1)%segments;faces.append((k,kn,kn+segments,k+segments))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=link(bpy.data.objects.new(floorid+' | V2 '+name,me),ma)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 return o

def piping(name,x,y,z,w,d,r=.09,ma='Linen piping'):
 pts=[]
 for cx,cy,a0 in [(x+w/2-r,y+d/2-r,0),(x-w/2+r,y+d/2-r,90),(x-w/2+r,y-d/2+r,180),(x+w/2-r,y-d/2+r,270)]:
  for i in range(7):a=math.radians(a0+i*90/6);pts.append(V(cx+r*cos(a),cy+r*sin(a),z))
 return tube(name,pts,.0028,ma,True)

def cloth(name,w,d,z,y=0,drop=.1,ma='Fabric ivory',nx=36,ny=32):
 vs=[];fs=[]
 for j in range(ny+1):
  v=j/ny*2-1
  for i in range(nx+1):
   u=i/nx*2-1;zz=z-drop*(abs(u)**14)-drop*.45*(max(0,-v)**12)+.005*sin(23*u+4*v)+.004*sin(41*v+2*u)
   vs.append(V(w*u/2,y+d*v/2,zz))
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);o=link(bpy.data.objects.new(floorid+' | V2 '+name,me),ma)
 for p in me.polygons:p.use_smooth=True
 mod=o.modifiers.new('Soft fabric thickness','SOLIDIFY');mod.thickness=.015
 mod=o.modifiers.new('Relaxed cloth surface','SUBSURF');mod.levels=1;mod.render_levels=1
 return o

mat('Linen piping',(.43,.40,.35),.9)
mat('Bronze trim',(.19,.14,.085),.35,.65)
mat('Dark grout',(.28,.29,.28),.9)
mat('Pool grout',(.48,.63,.60),.8)
mat('Mirror silver',(.82,.84,.85),.025,1)
mat('Satin porcelain',(.83,.83,.78),.25)
mat('Glassware',(.92,.98,1),.035,0,1)
M['Glassware'].node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.45
mat('Coffee',(.036,.015,.006),.22)
mat('Cushion ochre',(.29,.19,.09),.9)
mat('Leaf silver',(.22,.30,.15),.8)
mat('Window gasket',(.013,.018,.018),.85)
mat('Leather',(.12,.072,.04),.72)

# Maintain original chair, sofa and cabinet envelopes, adding construction details.
def sofa(x=0,y=0,width=3,ma='Fabric ivory'):
 _v1_sofa(x,y,width,ma)
 for i in range(3):
  xx=x+(i-1)*(width-.5)/3;piping('Sofa cushion welt',xx,y-.04,.648,(width-.52)/3-.025,.76,.07)
  B('V2 individual back cushion',(xx,y+.27,.83),((width-.5)/3-.035,.19,.42),ma,.085)
 for xx in [x-width*.33,x+width*.33]:
  B('V2 lumbar cushion',(xx,y+.10,.72),(.43,.20,.24),'Cushion ochre',.085,12)
 for xx in [x-width*.39,x+width*.39]:
  for yy in [y-.33,y+.33]:CY('V2 inset sofa leg',(xx,yy,.075),.026,.15,'Bronze trim')

def chair(x=0,y=0,angle=0,ma='Fabric ivory'):
 _v1_chair(x,y,angle,ma)
 oldO,oldA=O.copy(),A;globals()['O']=V(x,y,0);globals()['A']=A+math.radians(angle)
 piping('Dining seat welt',0,0,.534,.52,.53,.065)
 for xx in [-.2,.2]:B('V2 chair side stretcher',(xx,0,.17),(.027,.44,.027),'Oak',.005)
 globals()['O'],globals()['A']=oldO,oldA

def armchair(x=0,y=0,angle=0):
 _v1_armchair(x,y,angle)
 oldO,oldA=O.copy(),A;globals()['O']=V(x,y,0);globals()['A']=A+math.radians(angle)
 piping('Armchair seat welt',0,-.03,.583,.61,.62,.07)
 B('V2 lounge lumbar cushion',(0,.16,.71),(.47,.17,.23),'Cushion ochre',.075)
 globals()['O'],globals()['A']=oldO,oldA

def bed(f,x,y,angle=0,single=False):
 before=set(bpy.data.objects);_v1_bed(f,x,y,angle,single);w=1.1 if single else 1.9
 for o in set(bpy.data.objects)-before:
  if any(k in o.name for k in ['Bed cover','Throw folded over bed','Bedside lamp shade']):bpy.data.objects.remove(o,do_unlink=True)
 cloth('Draped duvet',w+.08,1.56,.754,-.28,.15)
 cloth('Folded woven throw',w+.09,.52,.785,-.78,.14,'Fabric grey',36,14)
 piping('Mattress seam',0,0,.628,w-.04,2.03,.13)
 for xx in [-w*.24,w*.24] if not single else [0]:
  piping('Pillow stitched edge',xx,.67,.8,.62,.38,.085)
  B('V2 second pillow',(xx,.85,.82),(.64,.36,.17),'Fabric ivory',.085,5)
 for xx in [-w/2-.43,w/2+.43]:
  lathe('Open linen lamp shade',[(.145,.785),(.18,1.02),(.173,1.02),(.14,.785)],(xx,.65,0),'Fabric ivory')
  CY('V2 lamp warm core',(xx,.65,.895),.055,.13,'Light warm')
  B('V2 bedside drawer seam',(xx,.391,.34),(.49,.008,.01),'Dark grout',.001)
  B('V2 bedside drawer pull',(xx,.377,.29),(.13,.022,.019),'Bronze trim',.006)
  B('V2 bedside book',(xx,.63,.593),(.23,.17,.025),'Paper',.003,12)
 # padded headboard inserts with restrained vertical stitching
 for i in range(4 if not single else 2):
  n=4 if not single else 2;xx=-w/2+(i+.5)*w/n
  B('V2 upholstered headboard panel',(xx,.988,.98),(w/n-.015,.035,1.20),'Fabric grey',.016)

def glassware(x,y,z):
 lathe('Water glass',[(.025,0),(.039,.004),(.038,.105),(.034,.11),(.032,.102),(.029,.011),(.025,.011)],(x,y,z),'Glassware',32)

def table(x=0,y=0,length=3.2,width=1.15,outdoor=False):
 B('Dining table top',(x,y,.77),(length,width,.085),'Oak',.04)
 B('V2 dining top underside reveal',(x,y,.715),(length-.12,width-.1,.025),'Dark grout',.009)
 for xx in [-length*.34,length*.34]:B('Dining table pedestal',(x+xx,y,.35),(.14,width*.64,.7),'Bronze trim',.02)
 n=4 if length>3.3 else 3
 for i in range(n):
  xx=x+(i-(n-1)/2)*.70
  for sign in [-1,1]:
   chair(xx,y+sign*(width/2+.4),0 if sign>0 else 180)
   B('V2 linen placemat',(xx,y+sign*width*.30,.817),(.49,.34,.004),'Fabric grey',.005)
   lathe('Rimmed dinner plate',[(0,.002),(.10,.002),(.143,.018),(.143,.026),(.12,.026),(.085,.013),(0,.013)],(xx,y+sign*width*.30,.82),'Porcelain',48)
   B('V2 folded napkin',(xx,y+sign*width*.30,.851),(.12,.20,.012),'Fabric ivory',.004,5)
   B('V2 cutlery',(xx+.19,y+sign*width*.30,.831),(.017,.2,.008),'Brass',.003)
   glassware(xx+.19,y+sign*.09,.82)
 lathe('Ceramic centre vase',[(0,0),(.07,0),(.10,.09),(.085,.20),(.052,.25),(.043,.25),(.05,.20),(.086,.09),(.054,.01),(0,.01)],(x,y,.82),'Limestone')

def coffee(x=0,y=0):
 CY('Coffee table oak base',(x,y,.185),.43,.34,'Oak');CY('Coffee table stone top',(x,y,.39),.69,.075,'Limestone')
 CY('V2 coffee tabletop bronze reveal',(x,y,.345),.64,.015,'Bronze trim')
 B('Coffee book',(x+.13,y,.445),(.31,.24,.032),'Paper',.004,8)
 B('V2 lower coffee book',(x+.15,y+.02,.433),(.34,.25,.018),'Fabric grey',.002,-4)
 lathe('Hollow coffee cup',[(0,0),(.046,0),(.056,.085),(.051,.091),(.047,.082),(.038,.01),(0,.01)],(x-.26,y,.43),'Porcelain',40)
 CY('V2 coffee surface',(x-.26,y,.496),.046,.003,'Coffee')
 pts=[V(x-.207+.026*cos(a),y,.48+.03*sin(a)) for a in [i*2*pi/24 for i in range(24)]];tube('Cup handle',pts,.007,'Porcelain',True)

def cabinet(x,y,length=3,height=2.55,ma='Oak'):
 _v1_cabinet(x,y,length,height,ma)
 B('V2 recessed cabinet kick',(x,y-.309,.055),(length-.08,.013,.08),'Dark grout',.003)
 B('V2 cabinet top reveal',(x,y-.318,height-.028),(length-.025,.01,.01),'Dark grout',.002)

def kitchen(f,x,y,angle=0):
 _v1_kitchen(f,x,y,angle)
 # Metal sink sidewalls and recessed bowl visible below a thin rim.
 for xx in [.987,1.613]:B('V2 sink side',(xx,1.55,.933),(.018,.42,.08),'Brass',.003)
 tube('Kitchen swan-neck faucet',[V(1.3,1.76,1.06),V(1.3,1.76,1.28),V(1.3,1.72,1.34),V(1.3,1.53,1.34),V(1.3,1.49,1.30)],.018,'Brass')
 for xx in [-.83,-.37]:
  for yy in [1.44,1.69]:
   pts=[V(xx+.085*cos(i*pi/20),yy+.085*sin(i*pi/20),.989) for i in range(40)];tube('Hob burner marking',pts,.0015,'Limestone',True)
 B('V2 oven handle',(-2.7,1.209,1.58),(.51,.037,.029),'Brass',.009)
 B('V2 oven control strip',(-2.7,1.23,1.735),(.64,.023,.05),'Charcoal metal',.004)
 for xx in [-2.93,-2.47]:
  o=CY('V2 oven dial',(xx,1.208,1.735),.017,.023,'Brass');o.rotation_euler.x=pi/2
 B('V2 kitchen backsplash',(0,1.925,1.14),(4.98,.018,.32),'Limestone',.003)
 B('V2 island toe recess',(0,-.807,.09),(3.40,.012,.075),'Dark grout',.004)
 for xx in [-1.15,0,1.15]:
  pts=[V(xx+.20*cos(i*pi/20),-1.48+.20*sin(i*pi/20),.25) for i in range(40)];tube('Stool footrest',pts,.014,'Charcoal metal',True)

# Sanitware shells replace the original solid demonstration blocks.
def bath(f,x,y,angle=0,tub=True):
 before=set(bpy.data.objects);_v1_bath(f,x,y,angle,tub)
 for o in set(bpy.data.objects)-before:
  if 'Washbasin' in o.name or 'Mirror' in o.name or 'Tub outer shell' in o.name or 'Tub inner water' in o.name:bpy.data.objects.remove(o,do_unlink=True)
 B('V2 silvered mirror',(0,.304,1.66),(1.52,.022,1.02),'Mirror silver',.012)
 for xx in [-.42,.42]:
  o=lathe('Hollow washbasin',[(0,0),(.10,0),(.15,.055),(.18,.12),(.17,.128),(.14,.06),(.085,.018),(0,.018)],(xx,-.02,.917),'Satin porcelain');
  # Shape elliptical bowls in world axes, retaining the original basin footprint.
  centre=V(xx,-.02,.917)
  for v in o.data.vertices:
   rel=v.co-centre;u=Vector((cos(A),sin(A),0));v.co+=u*(rel.dot(u)*.30)
  tube('Vanity curved tap',[V(xx,.20,1.02),V(xx,.20,1.21),V(xx,.12,1.24),V(xx,.02,1.24)],.014,'Brass')
 if tub:
  # rounded open bath shell defined by nested rounded-rectangle rings
  rings=[(.88,1.73,.08),(.94,1.78,.59),(.81,1.63,.64),(.67,1.46,.56),(.56,1.29,.15)]
  vs=[];fs=[];N=64
  for w,d,z in rings:
   for i in range(N):
    a=2*pi*i/N;xx=math.copysign(abs(cos(a))**.4,cos(a))*w/2;yy=math.copysign(abs(sin(a))**.4,sin(a))*d/2;vs.append(V(-1.5+xx,-1.6+yy,z))
  for j in range(len(rings)-1):
   for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
  fs.append(tuple(range((len(rings)-1)*N,len(rings)*N)))
  me=bpy.data.meshes.new('Open bath');me.from_pydata(vs,[],fs);o=link(bpy.data.objects.new(f+' | V2 open freestanding bath',me),'Satin porcelain')
  for p in me.polygons:p.use_smooth=True
  tube('Freestanding bath filler',[V(-.88,-1.5,0),V(-.88,-1.5,.92),V(-1.15,-1.5,.92)],.024,'Brass')
 tube('Shower riser',[V(-1.4,1.40,.9),V(-1.4,1.40,2.1),V(-1.4,1.14,2.15)],.018,'Brass')
 CY('V2 rainfall shower',(-1.4,1.08,2.12),.13,.026,'Brass')
 for yy in [.47,1.30]:B('V2 glass shower clip',(-.788,yy,1.8),(.04,.045,.035),'Brass',.005)
 B('V2 vanity towel',(.38,-.303,.6),(.38,.014,.32),'Fabric ivory',.014)

# Each plant is a single efficient leaf mesh with curved, individually oriented leaves.
def plant(f,x,y,height=1.4,site=False):
 global CUR
 at(f,x,y)
 if site:CUR=land
 p=O.copy();lathe('Tapered limestone planter',[(0,0),(.29,0),(.33,.04),(.38,.51),(.39,.55),(.355,.55),(.345,.50),(.285,.06),(0,.06)],ma='Limestone')
 CY('V2 planter soil',(0,0,.505),.348,.015,'Bark')
 tube('Olive trunk',[V(0,0,.50),V(.035,-.02,.8),V(-.03,.01,.5+height*.60)],.024,'Bark')
 verts=[];faces=[];mi=[]
 for branch in range(7):
  a=branch*2.399;end=Vector((.35*cos(a),.35*sin(a),.6+height*(.45+.055*branch)))
  start=Vector((0,0,.55+height*.27));tube('Olive branch',[V(*start),V(*(end*.6+start*.4)),V(*end)],.009,'Bark')
  for k in range(24):
   t=.25+.75*random.random();base=start.lerp(end,t)+Vector((random.uniform(-.18,.18),random.uniform(-.18,.18),random.uniform(-.13,.2)))
   aa=random.random()*2*pi;length=random.uniform(.10,.18);width=length*.27
   along=Vector((cos(aa),sin(aa),random.uniform(-.4,.6))).normalized()*length;side=Vector((-sin(aa),cos(aa),0))*width
   n=len(verts)
   for q in [base-along*.3,base+side,base+along*.6+Vector((0,0,.013)),base-side,base+along]:verts.append(V(*q))
   faces.extend([(n,n+1,n+2),(n,n+2,n+3),(n+1,n+4,n+2),(n+2,n+4,n+3)]);mi.extend([branch%3]*4)
 me=bpy.data.meshes.new('V2 olive leaf clusters');me.from_pydata(verts,[],faces);o=bpy.data.objects.new(f+' | V2 individually shaped olive foliage',me);CUR.objects.link(o)
 for ma in ['Leaves','Leaves light','Leaf silver']:me.materials.append(M[ma])
 for p,idx in zip(me.polygons,mi):p.material_index=idx;p.use_smooth=True


def refine_architecture_v2():
 bpy.context.view_layer.update()
 # Add edge details to existing elements using their own local coordinates.
 originals=list(scene.objects)
 for o in originals:
  if o.type!='MESH':continue
  cols=[c.name for c in o.users_collection];fc=next((c for c in cols if ' / ' in c),None)
  if not fc:continue
  f,cat=fc.split(' / ',1)
  if f not in floors:continue
  setfloor(f,'Details')
  dims=o.dimensions;matrix=o.matrix_world.copy()
  def local_box(n,xyz,size,ma,bev=.002):
   p=matrix@Vector(xyz);q=box('V2 '+n,p,size,ma,bev);q.rotation_euler=o.rotation_euler;return q
  if 'Vertical aluminium mullion' in o.name:
   for yy in [-.061,.061]:local_box('window EPDM gasket',(0,yy,0),(.033,.014,max(.1,dims.z-.035)),'Window gasket')
  elif 'Double glazing' in o.name:
   # Thin dry glazing beads define a clear frame-to-glass rebate.
   length=o.data.vertices and max(v.co.x for v in o.data.vertices)-min(v.co.x for v in o.data.vertices)
   if length:
    for side in [-1,1]:local_box('glazing bead',(side*(length/2-.012),-.023,0),(.022,.024,2.61),'Charcoal metal')
   if '1F'==f and o.location.z<5 and int(abs(o.location.x)*10)%9==0:
    local_box('sliding door grip',(max(-.25,-length/2+.13),-.065,-.31),(.025,.065,.38),'Bronze trim',.007)
  elif 'Open door leaf' in o.name:
   # A pair of lever handles remains within the existing door leaf envelope.
   for sign in [-1,1]:
    local_box('door lever backplate',(.30,sign*.035,-.08),(.036,.015,.13),'Bronze trim',.008)
    local_box('door lever handle',(.24,sign*.070,-.045),(.14,.026,.022),'Bronze trim',.008)
  elif 'Square structural pier' in o.name:
   local_box('pier base shadowline',(0,0,-dims.z/2+.075),(dims.x+.012,dims.y+.012,.018),'Dark grout')
  elif 'Balustrade laminated glass' in o.name:
   length=max(v.co.x for v in o.data.vertices)-min(v.co.x for v in o.data.vertices)
   for xx in [-length*.32,length*.32]:local_box('glass railing clamp',(xx,0,-.43),(.08,.06,.09),'Charcoal metal',.007)
  elif 'Stair ' in o.name and 'tread ' in o.name:
   local_box('stair inset anti-slip nosing',(0,-.10,dims.z/2+.002),(1.27,.018,.004),'Bronze trim',.001)
 # Narrow metal copings and shadow reveals retain every roof setback.
 for f,pts,h in [('3F',outline3,9.45),('2F',outline2,6.3)]:
  setfloor(f,'Details')
  for a,b in zip(pts,pts[1:]+pts[:1]):
   beam('V2 continuous fascia shadow rebate',P(*a,h-.21),P(*b,h-.21),.013,.027,'Dark grout',.003)
   if f=='3F':beam('V2 parapet metal coping',P(*a,h+.513),P(*b,h+.513),.245,.034,'Limestone',.009)
 # Slim roof drainage strips remain inside the parapet, no new roof structures.
 setfloor('3F','Details')
 for a,b in [((691,226),(691,1015)),((1439,596),(1439,1015)),((993,436),(1360,436))]:beam('V2 roof drainage channel',P(*a,9.454),P(*b,9.454),.05,.008,'Dark grout',.001)
 for x,y in [(701,1008),(1433,1008),(995,442)]:
  pb('V2 roof drain grille',x-2,y-2,x+2,y+2,9.454,.012,'Charcoal metal',.003)
 # Duct-free decorative ceiling reveals at important rooms, placed along walls.
 for f,name in [('1F','家庭客厅'),('1F','餐厅'),('2F','主卧'),('2F','主卧起居室')]:
  setfloor(f,'Ceilings');rr=next(r for r in rooms if r['floor']==f and r['name']==name);x1,y1,x2,y2=rr['reference_rect'];pts=rect(x1+3,y1+3,x2-3,y2-3)
  for a,b in zip(pts,pts[1:]+pts[:1]):
   beam('V2 perimeter ceiling reveal',P(*a,Z+2.855),P(*b,Z+2.855),.028,.018,'Dark grout',.003)
   beam('V2 recessed warm cove',P(*a,Z+2.847),P(*b,Z+2.847),.01,.008,'Light warm',.002)
 # Pool overflow grilles follow existing boundaries, with metre-sized tiling via PBR.
 for f,pts,z in [('1F',poolpoly,3.15-.14),('2F',rect(712,228,956,292),6.3-.13),('B1',rect(758,167,834,407),.15)]:
  setfloor(f,'Pools')
  for a,b in zip(pts,pts[1:]+pts[:1]):
   av,bv=Vector(P(*a,z+.18)),Vector(P(*b,z+.18));v=bv-av
   for i in range(max(1,int(v.length/.14))):
    pp=av+v*(i+.5)/max(1,int(v.length/.14));o=box('V2 coping expansion joint',pp,(.004,.29,.002),'Dark grout',0);o.rotation_euler.z=math.atan2(v.y,v.x)
 # Shower panel handles and equipment ventilation slots complete smaller spaces.
 for o in originals:
  if o.type!='MESH' or 'MEP cabinet' not in o.name:continue
  f=next((c.name.split(' / ')[0] for c in o.users_collection if ' / ' in c.name),'B1');setfloor(f,'Details')
  for i in range(8):
   pos=o.matrix_world@Vector((0,-.384,-.35+i*.06));q=box('V2 equipment ventilation grille',pos,(.7,.01,.017),'Charcoal metal',.002);q.rotation_euler=o.rotation_euler
 # Folded curtains stay at existing window corners, leaving the glazing open.
 for f,x,y,height in [('1F',968,445,5.75),('1F',1134,445,5.75),('2F',786,339,2.7),('2F',918,339,2.7)]:
  at(f,x,y);vs=[];fs=[];nx=36;nz=16
  for j in range(nz+1):
   t=j/nz
   for i in range(nx+1):
    u=i/nx;vs.append(V((u-.5)*(.44+.05*(1-t)),.065*sin(u*8*pi),.03+t*height))
  for j in range(nz):
   for i in range(nx):k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
  me=bpy.data.meshes.new('Folded curtain');me.from_pydata(vs,[],fs);o=link(bpy.data.objects.new(f+' | V2 folded linen curtain',me),'Fabric ivory')
  for pp in me.polygons:pp.use_smooth=True
  mod=o.modifiers.new('Curtain fabric thickness','SOLIDIFY');mod.thickness=.004
  tube('Curtain track',[V(-.30,0,height+.05),V(.30,0,height+.05)],.012,'Charcoal metal')
 # Pendant task lights over the existing west-kitchen island.
 at('1F',774,501,90);CUR=C['1F','Ceilings']
 for xx in [-1.1,1.1]:
  tube('Kitchen pendant suspension',[V(xx,-.25,2.84),V(xx,-.25,2.52)],.004,'Charcoal metal')
  lathe('Kitchen pendant shade',[(.075,2.52),(.14,2.35),(.132,2.345),(.066,2.52)],(xx,-.25,0),'Charcoal metal')
  CY('V2 pendant diffuser',(xx,-.25,2.345),.126,.012,'Light warm')
 # Fine grid joints stay confined to the existing outdoor paving bands.
 setfloor('1F','Details')
 for x1,y1,x2,y2 in [(637,185,693,1078),(978,344,1317,424),(1445,884,1494,1078)]:
  for xx in range(x1+15,x2,15):beam('V2 exterior paving joint',P(xx,y1,Z+.032),P(xx,y2,Z+.032),.004,.003,'Dark grout',0)
  for yy in range(y1+15,y2,15):beam('V2 exterior paving joint',P(x1,yy,Z+.032),P(x2,yy,Z+.032),.004,.003,'Dark grout',0)
 print('V2 architectural detailing complete',len(scene.objects),flush=True)


def finish_materials_v2():
 textures=Path(ROOT)/'textures'
 configs={'Warm plaster':('plaster',1),'Limestone':('limestone',1.2),'Stone floor':('limestone',.8),'Roof membrane':('plaster',2),'Oak':('oak',2.4),'Fabric ivory':('linen',.45),'Fabric grey':('linen_grey',.45),'Rug':('linen',.7),'Pool tile':('pool_mosaic',.6),'Water':('water',2.5)}
 for name,(tex,size) in configs.items():
  m=M[name];ns=m.node_tree.nodes;ls=m.node_tree.links;p=ns.get('Principled BSDF')
  for socket in ['Base Color','Normal','Roughness']:
   for link_ in list(p.inputs[socket].links):ls.remove(link_)
  for kind in ['color','normal','rough']:
   path=textures/(tex+'_'+kind+('.png' if kind=='normal' else '.jpg'));im=bpy.data.images.load(str(path),check_existing=True);im.pack();im.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color'
   n=ns.new('ShaderNodeTexImage');n.image=im;n.label='V2 portable '+kind
   if kind=='color':
    ls.new(n.outputs['Color'],p.inputs['Base Color'])
   elif kind=='normal':
    normal=ns.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.10 if name=='Water' else .18;ls.new(n.outputs['Color'],normal.inputs['Color']);ls.new(normal.outputs['Normal'],p.inputs['Normal'])
   else:ls.new(n.outputs['Color'],p.inputs['Roughness'])
 # Unique shared meshes need UVs once. Box projection uses physical metres, not bounding-box fitting.
 seen=set()
 for o in scene.objects:
  if o.type!='MESH' or o.data in seen:continue
  seen.add(o.data);me=o.data
  uv=me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
  for poly_ in me.polygons:
   mat_=me.materials[poly_.material_index] if len(me.materials)>poly_.material_index else None
   sz=configs.get(mat_.name if mat_ else '',('',1))[1];axis=max(range(3),key=lambda i:abs(poly_.normal[i]))
   axes=(0,1) if axis==2 else ((1,2) if axis==0 else (0,2))
   if mat_ and mat_.name=='Oak' and axis==2:axes=(1,0)
   for li in poly_.loop_indices:
    v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/sz,v[axes[1]]/sz)
 for im in bpy.data.images:
  if im.source=='FILE':im.pack()
 scene['v2_detail_scope']='Portable PBR textures; glazing seals and beads; roof copings and drainage; door hardware; soft fabric with seams and drapes; hollow sanitaryware and tableware; botanical leaf meshes; ceiling reveals and cove lighting.'
 print('V2 portable materials and UVs complete',len(seen),'meshes',flush=True)
