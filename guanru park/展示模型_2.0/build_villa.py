import bpy, math, os, json, random, sys
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from math import sin, cos, pi
random.seed(27)
ROOT=os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(ROOT,'qa'),exist_ok=True);os.makedirs(os.path.join(ROOT,'renders'),exist_ok=True)
S=1/18.75
# One shared coordinate system traced from the 2048x1152 reference display.
def P(x,y,z=0): return ((x-1068)*S,(622-y)*S,z)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.collections): bpy.data.collections.remove(d)
scene=bpy.context.scene; scene.name='00 · 完整建筑 | DAY'
scene.unit_settings.system='METRIC'; scene.unit_settings.length_unit='METERS'
M={}; C={}; floors={}; CUR=None; Z=0; floorid=''
def coll(name,parent=None):
 c=bpy.data.collections.new(name); (parent.children if parent else scene.collection.children).link(c); return c
for f,z in [('B1',0),('1F',3.15),('2F',6.3),('3F',9.45),('Roof',12.6)]:
 floors[f]=coll(f+' · '+{'B1':'康体娱乐与车库','1F':'公共起居与平台','2F':'卧室与退台','3F':'屋顶平台与局部房间','Roof':'顶层屋面'}[f])
 for cat in ['Structure','Windows','Furniture','Pools','Details','Labels']:
  C[f,cat]=coll(f+' / '+cat,floors[f])
land=coll('Site · 地面与少量绿植'); lightcol=coll('Lighting · 日景'); camcol=coll('Cameras · 展示视角'); refs=coll('References · 原图定位（默认隐藏）'); refs.hide_render=True; refs.hide_viewport=True

def setfloor(f,cat='Structure'):
 global CUR,Z,floorid
 CUR=C[f,cat]; Z={'B1':0,'1F':3.15,'2F':6.3,'3F':9.45,'Roof':12.6}[f];floorid=f

def mat(name,col,rough=.5,metal=0,trans=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Transmission Weight'].default_value=trans
 M[name]=m;return m
mat('Warm plaster',(.79,.77,.71),.78);mat('Limestone',(.61,.59,.52),.67);mat('Stone floor',(.68,.66,.60),.46);mat('Roof membrane',(.66,.65,.61),.78)
mat('Charcoal metal',(.045,.053,.055),.3,.72);mat('Clear glazing',(.83,.94,.95),.075,0,1);M['Clear glazing'].node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.46
mat('Oak',(.31,.18,.085),.48);mat('Fabric ivory',(.73,.69,.60),.92);mat('Fabric grey',(.28,.32,.32),.95);mat('Rug',(.45,.43,.36),1);mat('Porcelain',(.9,.89,.83),.22);mat('Pool tile',(.18,.49,.47),.38);mat('Water',(.27,.67,.68),.12,0,.85);M['Water'].node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.333
mat('Turf',(.16,.23,.13),1);mat('Leaves',(.13,.22,.105),.85);mat('Leaves light',(.26,.34,.14),.9);mat('Bark',(.17,.10,.058),1);mat('Asphalt',(.16,.17,.16),.95);mat('Ground',(.49,.49,.43),1);mat('Black screen',(.008,.017,.022),.24);mat('Brass',(.42,.29,.12),.3,.7);mat('Pool table felt',(.07,.21,.21),.94);mat('Paper',(.76,.74,.65),.9)
mat('Light warm',(.96,.76,.42),.3);p=M['Light warm'].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.72,.36,1);p.inputs['Emission Strength'].default_value=3
# restrained procedural, real-world scaled surface variation
for name,scale,strength in [('Warm plaster',34,.045),('Limestone',4,.065),('Stone floor',3,.024),('Oak',3,.035),('Fabric ivory',120,.10),('Fabric grey',100,.08),('Water',.9,.10)]:
 m=M[name];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2
 coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],tex.inputs['Vector']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=.025 if name!='Water' else .045;l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])

mat('Oak seam',(.26,.17,.092),.65)
m=M['Oak'];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1.1,20,1.2);l.new(coord.outputs['Object'],mapping.inputs[0]);grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=2.5;grain.inputs['Detail'].default_value=2;l.new(mapping.outputs[0],grain.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.15;r.color_ramp.elements[0].color=(.265,.159,.079,1);r.color_ramp.elements[1].position=.85;r.color_ramp.elements[1].color=(.35,.225,.122,1);l.new(grain.outputs['Fac'],r.inputs[0]);l.new(r.outputs['Color'],p.inputs['Base Color'])

def link(o,matname=None,col=None):
 (col or CUR).objects.link(o)
 if matname:o.data.materials.append(M[matname])
 o['level']=floorid
 return o
boxcache={}
def box(name,loc,size,ma='Warm plaster',bevel=.015,rot=0,col=None):
 key=(tuple(round(v,4) for v in size),ma,round(bevel,4))
 if key in boxcache: mesh=boxcache[key]
 else:
  x,y,z=[v/2 for v in size];vs=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)];fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
  fs=[tuple(reversed(f)) for f in fs]
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.materials.append(M[ma]);boxcache[key]=mesh
 o=bpy.data.objects.new(floorid+' | '+name,mesh);(col or CUR).objects.link(o);o.location=loc;o.rotation_euler.z=rot
 if bevel:
  mod=o.modifiers.new('Edge softness','BEVEL');mod.width=min(bevel,min(size)*.45);mod.segments=3
  mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def pb(name,x1,y1,x2,y2,z,h,ma='Warm plaster',bevel=.015):return box(name,P((x1+x2)/2,(y1+y2)/2,z+h/2),((x2-x1)*S,(y2-y1)*S,h),ma,bevel)
def poly(name,points,z,h,ma='Warm plaster',bevel=.01):
 pts=[P(x,y,z) for x,y in points]
 if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))<0:pts.reverse()
 n=len(pts);verts=pts+[(x,y,z+h) for x,y,z in pts]
 triangles=tessellate_polygon([[Vector(v) for v in pts]])
 # map coordinates back to input vertex indices
 lookup={tuple(v):i for i,v in enumerate(pts)}
 top=[tuple((v if isinstance(v,int) else min(range(n),key=lambda i:(Vector(pts[i])-v).length_squared))+n for v in t) for t in triangles]
 fs=[tuple(reversed(tuple(i-n for i in t))) for t in top]+top+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],fs);mesh.update();o=link(bpy.data.objects.new(floorid+' | '+name,mesh),ma)
 if bevel:mod=o.modifiers.new('Fine slab edges','BEVEL');mod.width=bevel;mod.segments=2
 return o

def cut(o,points,z,h):
 q=poly('TEMP opening',points,z,h,bevel=0);mod=o.modifiers.new('Actual opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=q
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(q,do_unlink=True)
def rect(x1,y1,x2,y2):return [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
def beam(name,a,b,width,height,ma='Warm plaster',bevel=.01):
 a,b=Vector(a),Vector(b);mid=(a+b)/2;v=b-a
 o=box(name,mid,(v.length,width,height),ma,bevel);o.rotation_euler=v.to_track_quat('X','Z').to_euler();return o

def cyl(name,loc,r,depth,ma='Charcoal metal',vertices=20,col=None):
 vs=[]
 for z in [-depth/2,depth/2]:
  for i in range(vertices):a=i*2*pi/vertices;vs.append((r*cos(a),r*sin(a),z))
 fs=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);o=link(bpy.data.objects.new(name,me),ma,col);o.location=loc
 for p in me.polygons:p.use_smooth=len(p.vertices)==4
 return o

def ball(name,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=loc);o=bpy.context.object;o.name=floorid+' | '+name
 for c in list(o.users_collection):c.objects.unlink(o)
 CUR.objects.link(o);o.scale=scale;o.data.materials.append(M[ma]);
 for p in o.data.polygons:p.use_smooth=True
 return o

def wall(a,b,door=None,ma='Warm plaster',h=2.89,t=.18):
 av,bv=Vector(P(*a,Z)),Vector(P(*b,Z));v=bv-av;length=v.length
 if door is None:beam('Partition',av+Vector((0,0,h/2)),bv+Vector((0,0,h/2)),t,h,ma)
 else:
  # door=(fraction,width); preserve a real gap, framed timber leaf opened 78 degrees
  f,w=door[:2];u=v.normalized();d=length*f;start=av+u*(d-w/2);end=av+u*(d+w/2)
  if d>w/2:beam('Partition beside door',av+Vector((0,0,h/2)),start+Vector((0,0,h/2)),t,h,ma)
  if length-d>w/2:beam('Partition beside door',end+Vector((0,0,h/2)),bv+Vector((0,0,h/2)),t,h,ma)
  beam('Door lintel',start+Vector((0,0,2.35+(h-2.35)/2)),end+Vector((0,0,2.35+(h-2.35)/2)),t,h-2.35,ma)
  beam('Door frame header',start+Vector((0,0,2.33)),end+Vector((0,0,2.33)),t+.03,.06,'Oak')
  for p in [start,end]:box('Door jamb',p+Vector((0,0,1.17)),(.065,t+.035,2.34),'Oak',.01,rot=math.atan2(v.y,v.x))
  if len(door)>2 and door[2]=='fixed':
   beam('Fixed observation glazing at void',start+u*.04+Vector((0,0,1.17)),end-u*.04+Vector((0,0,1.17)),.035,2.24,'Clear glazing',.002)
  else:
   theta=math.atan2(v.y,v.x)+math.radians(78);lc=start+Vector((cos(theta)*w/2,sin(theta)*w/2,1.16));box('Open door leaf',lc,(w-.05,.045,2.3),'Oak',.015,theta)
 # skirting follows full wall except opening
 for f1,f2 in ([(0,1)] if door is None else [(0,max(0,(length*door[0]-door[1]/2)/length)),(min(1,(length*door[0]+door[1]/2)/length),1)]):
  if f2>f1:beam('Stone skirting',av+v*f1+Vector((0,0,.06)),av+v*f2+Vector((0,0,.06)),t+.025,.12,'Limestone',.006)

def facade(a,b,mode='glass',h=2.89,base=None):
 z=Z if base is None else base;av,bv=Vector(P(*a,z)),Vector(P(*b,z));v=bv-av;L=v.length;u=v.normalized()
 if mode=='solid':beam('Opaque facade',av+Vector((0,0,h/2)),bv+Vector((0,0,h/2)),.26,h,'Warm plaster');return
 count=max(1,round(L/1.55));step=L/count
 for i in range(count):
  aa=av+u*i*step;bb=av+u*(i+1)*step
  beam('Double glazing',aa+u*.045+Vector((0,0,1.39)),bb-u*.045+Vector((0,0,1.39)),.032,2.66,'Clear glazing',.002)
 for i in range(count+1):
  p=av+u*i*step+Vector((0,0,1.4));box('Vertical aluminium mullion',p,(.075,.115,2.8),'Charcoal metal',.008,math.atan2(v.y,v.x))
 for hh in [.075,2.74]:beam('Glazing frame rail',av+Vector((0,0,hh)),bv+Vector((0,0,hh)),.13,.09,'Charcoal metal')
 beam('Facade head / soffit',av+Vector((0,0,2.835)),bv+Vector((0,0,2.835)),.28,.11,'Warm plaster')

def rail(points,z,glass=True):
 for a,b in zip(points[:-1],points[1:]):
  av,bv=Vector(P(*a,z)),Vector(P(*b,z));v=bv-av;L=v.length
  beam('Balustrade cap',av+Vector((0,0,1.08)),bv+Vector((0,0,1.08)),.05,.045,'Charcoal metal',.007)
  if glass:beam('Balustrade laminated glass',av+Vector((0,0,.55)),bv+Vector((0,0,.55)),.024,1.02,'Clear glazing',.002)
  for i in range(max(1,math.ceil(L/1.8))+1):
   p=av+v*i/max(1,math.ceil(L/1.8));box('Balustrade post',p+Vector((0,0,.54)),(.035,.035,1.08),'Charcoal metal',.006)

def perimeter(points,z,h=.5,ma='Warm plaster'):
 for a,b in zip(points,points[1:]+points[:1]):beam('Parapet',P(*a,z+h/2),P(*b,z+h/2),.20,h,ma)

# Exact reference footprint: west/south orthogonal edges + north-east quarter curve.
arc=[(960+545*sin(i*pi/2/48),730-580*cos(i*pi/2/48)) for i in range(49)]
sitepoly=[(630,150)]+arc+[(1505,1095),(630,1095)]
pool_end=(960+545*math.sqrt(1-((730-332)/580)**2),332)
poolpoly=[(1034,158)]+[p for p in arc if p[0]>1034 and p[1]<332]+[pool_end,(1034,332)]
ramppts=[(1142+108*cos(a),876+108*sin(a)) for a in [-pi/2+i*pi/48 for i in range(49)]]+[(1142+37*cos(a),876+37*sin(a)) for a in [pi/2-i*pi/48 for i in range(49)]]
# floors
setfloor('B1');base=poly('B1 foundation footprint',sitepoly,-.30,.30,'Limestone')
setfloor('1F');deck=poly('1F curved platform structural slab',sitepoly,Z-.28,.28,'Stone floor');cut(deck,poolpoly,Z-.7,1.4);cut(deck,ramppts,Z-.7,1.4)
for hole in [rect(746,658,812,730),rect(708,950,778,1022),rect(1252,914,1288,986)]:cut(deck,hole,Z-.7,1.4)
# H-shaped second floor / projecting terrace slabs
outline2=[(696,212),(972,212),(972,429),(1372,429),(1372,574),(1444,574),(1444,1034),(1240,1034),(1240,742),(972,742),(972,1034),(696,1034)]
setfloor('2F');slab2=poly('2F H footprint with open south court',outline2,Z-.27,.27,'Stone floor')
for hole in [rect(966,446,1136,582),rect(966,628,1066,728),rect(1148,628,1246,728),rect(710,954,778,1020),rect(1255,914,1284,986),rect(712,228,956,292)]:cut(slab2,hole,Z-.8,1.6)
outline3=[(684,210),(980,210),(980,428),(1376,428),(1376,574),(1452,574),(1452,1036),(1234,1036),(1234,742),(980,742),(980,1036),(684,1036)]
setfloor('3F');roof=poly('Broad H roof / 2F ceiling',outline3,Z-.27,.27,'Roof membrane')
# Plain reference roof: no additional skylight openings.
CUR=C['3F','Structure'];perimeter(outline3,Z,.5)
cut(roof,rect(1162,640,1224,726),Z-.7,1.4)
# B1 external elevations; pool tank forms solid curved sector
setfloor('B1','Windows')
facade((630,150),(960,150));facade((630,150),(630,1095),'solid');facade((630,1095),(1505,1095));facade((1505,730),(1505,1095))
# curve grouping gives regular wide openings and solid pool sector
for i in range(0,48,4):
 a,b=arc[i],arc[min(i+4,48)]
 if i<24:
  for j in range(i,min(i+4,48)):facade(arc[j],arc[j+1],'solid')
 elif i==24:
  facade(arc[24],pool_end,'solid');facade(pool_end,arc[28],'glass')
 else:facade(a,b,'glass' if (i//4)%3!=1 else 'solid')
# 1F external walls and piers traced around both wings, bridge, open court
setfloor('1F','Windows')
segments=[((708,332),(960,332),'glass'),((708,332),(708,730),'glass'),((708,730),(708,1022),'solid'),((708,1022),(960,1022),'glass'),((960,730),(960,1022),'glass'),((960,730),(1252,730),'glass'),((1252,730),(1252,1022),'glass'),((1252,1022),(1432,1022),'glass'),((1432,1022),(1432,586),'glass'),((1360,586),(1432,586),'glass'),((1360,440),(1360,586),'glass'),((960,440),(1360,440),'glass'),((960,332),(960,440),'glass')]
for a,b,t in segments:facade(a,b,t)
# opaque patches located at services / office as seen in elevations
for a,b in [((708,520),(708,554)),((708,650),(708,681)),((1324,440),(1358,440)),((1432,742),(1432,798)),((1432,813),(1432,863))]:facade(a,b,'solid')
setfloor('1F')
for x,y in [(708,224),(834,224),(960,224),(960,440),(1142,440),(1360,440),(708,586),(960,586),(1252,622),(1432,730)]:pb('Square structural pier',x-4,y-4,x+4,y+4,Z,2.89,'Limestone')
# 2F facades: north master bedroom recessed behind pool and terrace
setfloor('2F','Windows')
for a,b,t in [((708,440),(708,1022),'glass'),((708,1022),(936,1022),'glass'),((936,734),(936,1022),'glass'),((936,734),(1252,734),'glass'),((1252,734),(1252,986),'glass'),((1252,986),(1396,986),'glass'),((1396,986),(1396,878),'glass'),((1396,878),(1432,878),'solid'),((1432,878),(1432,734),'glass'),((1432,734),(1396,734),'solid'),((1396,734),(1396,586),'glass'),((1324,586),(1396,586),'glass'),((1324,478),(1324,586),'glass'),((1216,478),(1324,478),'glass'),((1216,440),(1216,478),'solid'),((960,440),(1216,440),'glass'),((960,334),(960,440),'glass'),((780,334),(924,334),'glass'),((780,334),(780,440),'glass'),((924,334),(924,440),'glass'),((708,440),(780,440),'glass'),((924,440),(960,440),'glass')]:facade(a,b,t)
for a,b in [((708,522),(708,585)),((708,626),(708,676)),((936,778),(936,801)),((936,850),(936,876)),((936,922),(936,946)),((1432,741),(1432,798)),((1432,813),(1432,868)),((1142,440),(1216,440))]:facade(a,b,'solid')
# corner projection fascia edges and terrace railings
setfloor('2F','Details')
for pts in [[(702,332),(702,216),(966,216),(966,430)],[(1246,1030),(1440,1030),(1440,578),(1368,578),(1368,434),(1218,434)],[(696,444),(696,1030),(972,1030),(972,742)],[(966,446),(966,582),(1136,582),(1136,446)],[(968,630),(968,726),(1064,726),(1064,630)],[(1148,630),(1148,726),(1244,726),(1244,681)]]:rail(pts,Z)
# 3F compact pavilion from external and roof axonometric, roof footprint intentionally local
setfloor('3F');pavilion=rect(960,586,1252,730)
pavfinish=pb('Roof pavilion finish',960,586,1252,730,Z,.03,'Stone floor')
cut(pavfinish,rect(1162,640,1224,726),Z-.3,.6)
CUR=C['3F','Windows']
for a,b,t in [((960,586),(1252,586),'glass'),((1252,586),(1252,730),'glass'),((1252,730),(960,730),'glass'),((960,730),(960,586),'solid'),((1070,586),(1142,586),'solid')]:facade(a,b,t)
setfloor('3F');wall((1070,622),(1070,730),(.60,.95));wall((1142,622),(1142,730),(.55,.95));wall((1070,622),(1142,622),(.45,.95))
rail([(1162,642),(1162,725),(1224,725),(1224,681)],Z)
setfloor('Roof');poly('Thin upper pavilion roof',rect(948,574,1264,742),Z-.18,.18,'Charcoal metal')
# Boundary retaining screens are on straight back edges, as reference; avoid burying exposed B1
setfloor('1F','Details');beam('West boundary screen',P(630,150,Z+1.05),P(630,1095,Z+1.05),.2,2.1);beam('South boundary screen',P(630,1095,Z+1.05),P(1505,1095,Z+1.05),.2,2.1)
# Safe low transparent protection along exposed curved platform, behind infinity edge
rail([(630,154),(960,154)],Z)
rail([p for p in arc if p[1]>337]+[(1501,1090)],Z)
# Primary internal partitions. End points follow the common plan grid.
W={
'B1':[
((704,150),(704,239),None),((704,258),(704,586),(.37,1)),((630,260),(704,260),None),((630,332),(704,332),(.75,.9)),((630,368),(684,368),None),((630,422),(704,422),(.8,.9)),((630,478),(684,478),None),((630,514),(704,514),(.8,.9)),
((740,150),(740,514),(.88,1.2)),((850,150),(850,440),None),((960,150),(960,586),(.56,1.3)),((1032,156),(1032,332),None),((850,332),(960,332),(.8,1.1)),((978,332),(1338,332),(.08,1.2)),((1338,332),(1338,440),(.74,.9)),((960,440),(1394,440),(.17,1.4)),
((740,514),(850,514),(.68,1.2)),((850,440),(850,586),(.34,1.2)),((630,586),(1126,586),(.53,1.4)),((1032,440),(1032,550),(.73,1)),((1032,550),(1138,550),None),((1138,440),(1138,586),None),((1248,440),(1248,730),(.57,1)),((1138,586),(1248,586),(.82,1)),((1138,622),(1138,730),(.69,1.2)),((1250,496),(1320,496),(.58,.9)),((1320,440),(1320,586),(.75,1)),((1342,586),(1464,586),None),
((630,696),(720,696),(.8,.9)),((740,622),(740,730),(.15,1.1)),((850,586),(850,730),(.57,1.2)),((630,730),(1080,730),(.28,1.2)),((1126,730),(1505,730),(.47,1.2)),((1080,622),(1080,730),(.55,1.4)),((850,622),(1080,622),(.34,1.4)),
((704,840),(704,1022),(.52,1)),((812,768),(812,876),(.53,.9)),((630,876),(812,876),None),((704,950),(850,950),(.82,1)),((850,730),(850,1095),(.64,1.2)),((704,1022),(850,1022),(.55,.9)),((740,1022),(740,1095),None),((776,1022),(776,1095),None),
((1250,734),(1250,878),(.63,1)),((1250,914),(1250,986),None),((1250,986),(1300,986),(.62,1)),((1320,730),(1320,1022),(.36,1)),((1360,730),(1360,804),None),((1414,730),(1414,804),None),((1360,804),(1505,804),(.65,.9)),((1320,914),(1466,914),(.27,1)),((1320,1022),(1505,1022),(.44,1)),((1414,1022),(1414,1095),None),((1360,1022),(1360,1095),None),((1466,804),(1466,1022),None)
],
'1F':[
((708,440),(960,440),(.8,1.3)),((850,440),(850,730),(.17,1.2)),((874,622),(1069,622),None),((888,622),(888,708),(.7,1)),((1069,622),(1069,730),(.55,1.1)),((850,730),(1069,730),(.1,1)),((960,440),(960,622),(.77,1.5)),
((1142,440),(1142,586),None),((1142,586),(1252,586),(.86,1)),((1252,440),(1252,622),(.8,1)),((1252,514),(1360,514),(.75,1)),((1288,460),(1288,514),None),((1252,622),(1396,622),None),((1288,622),(1288,714),(.86,1)),((1396,622),(1396,730),None),
((708,730),(850,730),(.7,1.2)),((812,768),(812,876),(.6,.95)),((728,840),(812,840),None),((708,876),(834,876),(.85,1)),((708,950),(850,950),(.82,1)),((850,730),(850,1022),(.48,1.1)),
((1288,730),(1432,730),(.22,1)),((1288,730),(1288,876),None),((1342,730),(1342,804),(.5,.95)),((1342,804),(1342,876),(.5,.95)),((1288,804),(1432,804),(.61,.95)),((1288,876),(1432,876),(.29,1)),((1288,876),(1288,986),(.27,1)),((1396,876),(1396,986),None),((1288,986),(1396,986),(.38,1)),((1252,914),(1288,914),(.5,.8))
],
'2F':[
((780,440),(924,440),(.38,1.1)),((816,440),(816,514),(.5,1)),((816,514),(960,514),(.82,1)),((780,514),(816,514),None),((780,514),(780,554),None),((780,586),(816,586),None),((816,586),(816,662),None),((780,662),(816,662),None),((780,696),(780,734),None),((816,554),(816,626),(.57,1)),((816,626),(924,626),None),((924,514),(924,734),(.75,1)),((816,698),(816,734),None),((708,734),(936,734),(.56,1.1)),
((960,440),(960,626),None),((960,586),(1136,586),(.63,1.4,'fixed')),((960,626),(1070,626),None),((1070,626),(1070,734),(.5,1,'fixed')),((1070,734),(1142,734),(.5,1.2)),((1142,626),(1252,626),None),((1142,626),(1142,734),None),
((1142,440),(1142,586),(.73,.9)),((1142,534),(1216,534),(.55,.9)),((1216,478),(1216,586),(.88,1)),((1252,586),(1304,586),None),((1288,586),(1288,714),(.7,1)),((1288,734),(1432,734),(.4,.95)),((1288,734),(1288,878),None),((1342,734),(1342,806),(.5,.95)),((1342,806),(1342,878),(.5,.95)),((1288,806),(1432,806),(.71,.95)),((1288,878),(1432,878),(.6,1)),
((816,734),(816,806),(.5,1)),((816,806),(816,878),(.5,1)),((816,878),(816,950),(.5,1)),((816,950),(816,1022),(.5,1)),((708,784),(816,784),(.78,1)),((816,806),(936,806),None),((816,878),(936,878),None),((816,950),(936,950),None),((708,954),(816,954),(.72,1)),((780,954),(780,1022),None)
]}
for f,lines in W.items():
 setfloor(f)
 for a,b,d in lines:wall(a,b,d)
# Actual double-height living room and two smaller voids, with horizontal circulation retained around them.
# floor coverings + room identifiers recorded for QA / editing
rooms=[]
def room(f,name,r,finish='Stone floor'):
 setfloor(f,'Details');x1,y1,x2,y2=r;pb(name+' | floor finish',x1+2,y1+2,x2-2,y2-2,Z+.004,.025,finish,.002)
 rooms.append({'floor':f,'name':name,'reference_rect':r,'approx_area_m2':round((x2-x1-4)*(y2-y1-4)*S*S,2)})
 # English and Chinese objects readable in outliner; numbered floor-plan labels
 setfloor(f,'Labels');cu=bpy.data.curves.new(name,'FONT');cu.body=f'{len([r for r in rooms if r["floor"]==f]):02d}';cu.size=.50;cu.align_x='CENTER';cu.align_y='CENTER';o=link(bpy.data.objects.new(name+' | plan key',cu),'Charcoal metal');o.location=P((x1+x2)/2,y2-12,Z+.05)
R={
'B1':[
('SPA',(630,150,704,260)),('热泡池',(630,260,704,332)),('康疗走廊',(704,150,740,586)),('桑拿房',(630,368,704,422)),('淋浴间',(630,514,704,586)),('室内泳池',(740,150,850,514)),('乒乓球室',(850,150,960,332)),('瑜伽房',(960,150,1032,332)),('保龄球道',(960,332,1338,440)),('健身房',(850,440,1032,586)),('模拟高尔夫',(1032,440,1138,550)),('酒窖',(1138,440,1248,586)),('影音室',(1248,496,1320,586)),('客卧1',(1320,440,1392,586)),('客卫1',(1342,354,1380,438)),('客房客厅',(1252,622,1464,730)),('娱乐大厅',(850,622,1080,730)),('沙龙',(630,586,718,696)),('西楼梯厅',(740,586,850,730)),('东楼梯厅',(1142,586,1248,730)),('家庭影院',(630,730,812,876)),('游戏厅',(630,878,812,1022)),('车库',(850,734,1138,1095)),('机电设备北',(1250,734,1320,878)),('客卧2',(1360,806,1466,914)),('客卧3',(1320,914,1466,1022)),('客卫2',(1414,734,1502,804)),('客卫3',(1414,1024,1502,1092)),('机电设备南',(1250,1024,1356,1092))],
'1F':[
('户外客餐区',(708,224,960,332)),('家庭客厅',(708,332,960,440)),('西厨及休闲餐厅',(708,440,850,656)),('餐厅',(850,440,960,622)),('主客厅',(960,440,1142,622)),('酒窖',(1142,440,1252,586)),('池畔酒吧',(1288,440,1360,514)),('起居室',(1252,514,1360,622)),('办公室',(888,622,1069,730)),('中厨',(708,730,850,840)),('洗衣房',(708,876,850,950)),('上层车库',(850,734,960,1022)),('次卧4',(1288,622,1396,730)),('次卫4',(1342,730,1432,804)),('次卫5',(1342,804,1432,876)),('次卧5',(1288,876,1396,986))],
'2F':[
('主卧',(780,334,924,440)),('主卧起居室',(816,440,960,514)),('主卫西区',(708,514,780,734)),('女士衣帽间',(816,514,924,626)),('男士衣帽间',(816,626,924,734)),('洗衣房',(1070,626,1142,734)),('次卧1',(1216,478,1324,586)),('次卫1',(1142,440,1216,534)),('次卧2',(1288,586,1396,734)),('次卫2',(1342,734,1432,806)),('次卫3',(1342,806,1432,878)),('次卧3',(1288,878,1396,986)),('员工公共区',(708,784,816,950)),('员工宿舍1',(816,734,936,806)),('员工宿舍2',(816,806,936,878)),('员工宿舍3',(816,878,936,950)),('员工宿舍4',(816,950,936,1022))]}
for f,rs in R.items():
 for name,r in rs:room(f,name,r,'Oak' if any(k in name for k in ['卧','宿舍','衣帽']) else 'Stone floor')
# Natural floorboard scale, approximately 200 mm wide, with staggered end joints.
for rr in rooms:
 if not any(k in rr['name'] for k in ['卧','宿舍','衣帽']):continue
 f=rr['floor'];setfloor(f,'Details');x1,y1,x2,y2=rr['reference_rect'];vs=[];fs=[]
 def seam(xa,ya,xb,yb,width=.065):
  i=len(vs)
  if abs(xa-xb)<.01:pts=[(xa-width/2,ya),(xa+width/2,ya),(xb+width/2,yb),(xb-width/2,yb)]
  else:pts=[(xa,ya-width/2),(xb,yb-width/2),(xb,yb+width/2),(xa,ya+width/2)]
  vs.extend(P(x,y,Z+.030) for x,y in pts);fs.append((i,i+1,i+2,i+3))
 yy=y1+2;row=0
 while yy<y2-2:
  seam(x1+2,yy,x2-2,yy);xx=x1+2+(row%3)*13.3
  while xx<x2-2:
   if xx>x1+2:seam(xx,yy,xx,min(y2-2,yy+3.75))
   xx+=40
  yy+=3.75;row+=1
 me=bpy.data.meshes.new('Floor plank joints');me.from_pydata(vs,[],fs);link(bpy.data.objects.new(f+' | '+rr['name']+' oak board seams',me),'Oak seam')
# Keep reference ambiguity editable rather than filling it with invented bedrooms.
for f,r in [('1F',(1145,625,1249,728)),('2F',(966,446,1136,582)),('2F',(966,628,1066,728)),('2F',(1148,628,1246,728))]:
 setfloor(f,'Labels');e=bpy.data.objects.new('ASSUMPTION · 挑空 / 以剖切图为准',None);CUR.objects.link(e);e.location=P((r[0]+r[2])/2,(r[1]+r[3])/2,Z);e['reference']='2F cutaway + floorplan void annotations';e['editable_assumption']=True
# pools have real shell, coping, water and step geometry

def pool(name,pts,surface,depth):
 floor=poly(name+' | tiled tank bottom',pts,surface-depth-.14,.14,'Pool tile')
 for a,b in zip(pts,pts[1:]+pts[:1]):
  beam(name+' | pool wall',P(*a,surface-depth/2),P(*b,surface-depth/2),.19,depth,'Pool tile',.02)
  beam(name+' | stone coping',P(*a,surface+.11),P(*b,surface+.11),.29,.14,'Limestone',.025)
 poly(name+' | water volume',pts,surface-.10,.10,'Water',.002)
 return floor
setfloor('1F','Pools');pool('Infinity pool · 原弧边水池',poolpoly,Z-.14,1.30)
for i in range(4):pb('Infinity pool submerged entry step',1035,285+i*8,1067,293+i*8,Z-.20-i*.25,.15,'Pool tile')
setfloor('B1','Pools');pool('Indoor lap pool',rect(758,167,834,407),Z+.15,1.15)
for i in range(4):pb('Indoor pool step',758,407+i*7,834,414+i*7,Z-.65+i*.23,.15,'Pool tile')
pool('Hot spa',rect(643,274,691,320),Z+.45,.65)
setfloor('2F','Pools');pool('Master terrace pool',rect(712,228,956,292),Z-.13,.60)
# A shallow relaxation pool retains clearance to the outdoor dining zone below.
for aa,bb in [((710,226),(958,226)),((710,226),(710,294)),((958,226),(958,294)),((710,294),(958,294))]:beam('Master pool external white tank fascia',P(*aa,Z-.40),P(*bb,Z-.40),.15,.88,'Warm plaster',.015)

# floor-by-floor human stairs in aligned rectangular openings

def stairs(f,x,y,w=1.65,run=3.3,rise=3.15):
 setfloor(f,'Structure');start=Vector(P(x,y,Z));n=9;fw=1.4;gap=.18;tread=.28;flight=n*tread;total=2*fw+gap;mid=rise/2
 for i in range(n):
  hh=rise*(i+1)/(2*n)
  box('Stair west flight tread %02d'%i,start+Vector((-(fw+gap)/2,-tread*(i+.5),hh-.09)),(fw,tread+.02,.18),'Limestone',.012)
  hh2=mid+rise*(i+1)/(2*n)
  box('Stair return flight tread %02d'%i,start+Vector(((fw+gap)/2,-flight+tread*(i+.5),hh2-.09)),(fw,tread+.02,.18),'Limestone',.012)
 box('Stair half-level landing',start+Vector((0,-flight-.50,mid-.10)),(total,1.0,.20),'Limestone',.012)
 for xx in [-total/2,-gap/2]:
  aa=start+Vector((xx,0,.95));bb=start+Vector((xx,-flight,mid+.95));beam('Stair rising handrail',aa,bb,.045,.045,'Charcoal metal',.008)
  for i in range(0,n+1,2):box('Stair west baluster',start+Vector((xx,-tread*i,rise*i/(2*n)+.48)),(.025,.025,.96),'Charcoal metal',.003)
 for xx in [gap/2,total/2]:
  stop=n-3 if xx==total/2 else n
  aa=start+Vector((xx,-flight,mid+.95));bb=start+Vector((xx,-flight+tread*stop,mid+rise*stop/(2*n)+.95));beam('Stair return handrail',aa,bb,.045,.045,'Charcoal metal',.008)
  for i in range(0,stop+1,2):box('Stair return baluster',start+Vector((xx,-flight+tread*i,mid+rise*i/(2*n)+.48)),(.025,.025,.96),'Charcoal metal',.003)
 for xx in [-total/2,total/2]:beam('Stair landing side handrail',start+Vector((xx,-flight,mid+.95)),start+Vector((xx,-flight-.97,mid+.95)),.045,.045,'Charcoal metal',.008)
 beam('Stair landing rear handrail',start+Vector((-total/2,-flight-.97,mid+.95)),start+Vector((total/2,-flight-.97,mid+.95)),.045,.045,'Charcoal metal',.008)
 for xx in [-total/2,0,total/2]:box('Stair landing baluster',start+Vector((xx,-flight-.97,mid+.48)),(.025,.025,.96),'Charcoal metal',.003)
 edge={744:778,779:812,1193:1246}.get(x,x+55);endx=(edge-x)*S+.10;beginx=total/2
 box('Stair upper side landing',start+Vector(((endx+beginx)/2,-.65,rise-.086)),(max(.20,endx-beginx),1.30,.18),'Limestone',.012)
for f in ['B1','1F']:stairs(f,744,952)
setfloor('2F','Details');rail([(778,989),(778,1018)],Z)
# The compact eastern opening is retained as a service void; human circulation uses the larger aligned cores.
stairs('2F',1193,643)
# road ramp: continuous half-annulus, not steps. Preserve traced footprint and expose its opening.
setfloor('B1');vs=[];N=80
for i in range(N+1):
 t=i/N;a=-pi/2+t*pi;zz=3.15*t
 for r in [37,108]:vs.append(P(1142+r*cos(a),876+r*sin(a),zz))
fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(N)];me=bpy.data.meshes.new('Continuous ramp mesh');me.from_pydata(vs,[],fs);o=link(bpy.data.objects.new('B1 → 1F | 半环形车辆坡道',me),'Asphalt');mod=o.modifiers.new('Ramp deck thickness','SOLIDIFY');mod.thickness=.22
# Continuous closed mesh guards avoid a false stair-like rhythm along the vehicle ramp.
for rad in [37,108]:
 verts=[];faces=[]
 for i in range(N+1):
  a=-pi/2+i*pi/N;zz=3.15*i/N
  for hh in [0,1]:
   for rr in [rad-.075/S,rad+.075/S]:verts.append(P(1142+rr*cos(a),876+rr*sin(a),zz+hh))
 for i in range(N):
  k=4*i;faces += [(k,k+4,k+5,k+1),(k+2,k+3,k+7,k+6),(k,k+2,k+6,k+4),(k+1,k+5,k+7,k+3)]
 faces += [(0,1,3,2),(4*N,4*N+2,4*N+3,4*N+1)]
 me=bpy.data.meshes.new('Continuous ramp guard mesh');me.from_pydata(verts,[],faces);me.update()
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 oo=link(bpy.data.objects.new('B1 | Ramp continuous guard wall',me),'Limestone')
 for j,pp in enumerate(me.polygons):pp.use_smooth=(j%4 in [2,3] and j<4*N)
 mod=oo.modifiers.new('Fine continuous edge','BEVEL');mod.width=.01;mod.segments=2
# clear flat transition aprons join the garage and 1F court
pb('Lower ramp transition',1102,752,1142,837,.005,.025,'Asphalt');setfloor('1F');pb('Upper ramp transition',1102,913,1142,1000,Z+.005,.025,'Asphalt')
# Open the central vertical circulation shown as grey / 洞 in the first-floor plan.
setfloor('1F');cut(deck,rect(1148,628,1246,728),Z-.8,1.6);rail([(1148,630),(1148,726),(1246,726),(1246,681)],Z)
stairs('B1',1193,643,1.8,3.35);stairs('1F',1193,643,1.8,3.35)
stairs('B1',779,662,1.8,3.2)
setfloor('1F','Details');rail([(748,727),(748,660),(811,660)],Z);rail([(811,694),(811,727)],Z)
setfloor('B1');cut(base,rect(758,167,834,407),-2,3);cut(base,rect(643,274,691,320),-2,3)
# Furniture uses metre dimensions and shared meshes; local assembly lets repeated sets stay consistent.
O=Vector((0,0,0));A=0

def at(f,x,y,angle=0):
 global O,A
 setfloor(f,'Furniture');O=Vector(P(x,y,Z+.035));A=math.radians(angle)
def V(x,y,z):return O+Vector((x*cos(A)-y*sin(A),x*sin(A)+y*cos(A),z))
def B(n,loc,sz,ma='Oak',bev=.025,angle=0):return box(n,V(*loc),sz,ma,bev,A+math.radians(angle))
def CY(n,loc,r,h,ma='Charcoal metal'):return cyl(n,V(*loc),r,h,ma)
def sofa(x=0,y=0,width=3,ma='Fabric ivory'):
 B('Sofa timber plinth',(x,y,.16),(width-.15,.86,.18),'Oak',.025)
 B('Sofa upholstered base',(x,y,.35),(width,1.03,.34),ma,.10)
 B('Sofa back',(x,y+.41,.70),(width,.24,.64),ma,.105)
 for xx in [x-width/2+.12,x+width/2-.12]:B('Sofa rounded arm',(xx,y,.6),(.24,1.02,.52),ma,.10)
 for i in range(3):B('Sofa seat cushion',(x+(i-1)*(width-.5)/3,y-.04,.57),((width-.52)/3-.025,.77,.20),ma,.08)
 for xx in [x-width*.3,x+width*.3]:B('Loose cushion',(xx,y+.24,.83),(.48,.18,.40),'Fabric grey',.085,10)

def chair(x=0,y=0,angle=0,ma='Fabric ivory'):
 oldO,oldA=O.copy(),A
 # rotate one chair around its own centre
 globals()['O']=V(x,y,0);globals()['A']=A+math.radians(angle)
 for xx in [-.22,.22]:
  for yy in [-.22,.22]:B('Chair tapered leg',(xx,yy,.24),(.045,.045,.48),'Oak',.008)
 B('Chair seat',(0,0,.48),(.55,.56,.13),ma,.06)
 B('Chair curved back',(0,.25,.75),(.55,.09,.46),ma,.045)
 globals()['O'],globals()['A']=oldO,oldA

def armchair(x=0,y=0,angle=0):
 oldO,oldA=O.copy(),A;globals()['O']=V(x,y,0);globals()['A']=A+math.radians(angle)
 for xx in [-.29,.29]:
  for yy in [-.29,.29]:B('Lounge chair oak foot',(xx,yy,.16),(.055,.055,.32),'Oak',.012)
 B('Lounge chair upholstered base',(0,0,.35),(.84,.83,.29),'Fabric ivory',.11)
 B('Lounge chair seat',(0,-.03,.51),(.62,.63,.17),'Fabric ivory',.075)
 B('Lounge chair back',(0,.31,.71),(.84,.19,.58),'Fabric ivory',.09)
 for xx in [-.355,.355]:B('Lounge chair arm',(xx,0,.59),(.15,.82,.36),'Fabric ivory',.065)
 globals()['O'],globals()['A']=oldO,oldA

def small_living(f,x,y,angle=0):
 at(f,x,y,angle);B('Small sitting rug',(0,-.6,.025),(3.5,3.25,.035),'Rug',.025);sofa(0,.70,2.4);coffee(0,-.90);armchair(-1.05,-.92,40)
 B('Sitting room console',(0,-2.55,.33),(2.5,.4,.6),'Oak',.025)

def table(x=0,y=0,length=3.2,width=1.15,outdoor=False):
 B('Dining table top',(x,y,.77),(length,width,.08),'Oak',.04)
 for xx in [-length*.34,length*.34]:B('Dining table pedestal',(x+xx,y,.37),(.16,width*.62,.74),'Charcoal metal',.02)
 n=4 if length>3.3 else 3
 for i in range(n):
  xx=x+(i-(n-1)/2)*.70
  chair(xx,y+width/2+.40,0);chair(xx,y-width/2-.40,180)
 # restrained dining accessories
 for xx in [-.55,.55]:CY('Stoneware plate',(x+xx,y,.825),.14,.018,'Porcelain')
 CY('Table vase',(x,y,.96),.09,.28,'Limestone')

def coffee(x=0,y=0):
 CY('Coffee table oak base',(x,y,.19),.46,.34,'Oak');CY('Coffee table stone top',(x,y,.39),.69,.075,'Limestone')
 B('Coffee book',(x+.16,y,.445),(.29,.22,.035),'Paper',.004)
 CY('Coffee cup',(x-.25,y,.48),.055,.09,'Porcelain')

def living(f,x,y,angle=0):
 at(f,x,y,angle);B('Woven living rug',(0,-.9,.025),(4.9,4.1,.035),'Rug',.025);sofa(0,.70,3.25);coffee(0,-1.05);armchair(-2.0,-1,60);armchair(2.0,-1,-60)
 B('Low media console',(0,-3.18,.32),(3.6,.44,.57),'Oak',.035);B('TV / display',(0,-3.32,1.15),(1.75,.06,1.0),'Black screen',.025)
 CY('Side table',(-2,.65,.38),.35,.05,'Limestone');CY('Side table stem',(-2,.65,.19),.035,.38)

def bed(f,x,y,angle=0,single=False):
 at(f,x,y,angle);w=1.1 if single else 1.9
 B('Bedroom rug',(0,-.35,.025),(w+1.5,3.5,.03),'Rug',.02)
 B('Bed recessed foot',(0,0,.16),(w-.2,1.9,.25),'Oak',.035);B('Bed upholstered frame',(0,0,.32),(w+.14,2.2,.32),'Fabric grey',.09)
 B('Bed mattress',(0,0,.57),(w,2.06,.25),'Fabric ivory',.11);B('Bed cover',(0,-.25,.70),(w+.03,1.45,.09),'Fabric ivory',.065)
 B('Throw folded over bed',(0,-.73,.756),(w+.06,.55,.045),'Fabric grey',.035)
 B('Headboard',(0,1.08,.92),(w+.3,.15,1.4),'Oak',.045)
 for xx in ([-w*.24,w*.24] if not single else [0]):B('Pillow',(xx,.67,.765),(.65,.40,.14),'Fabric ivory',.10)
 for xx in [-w/2-.43,w/2+.43]:
  B('Bedside cabinet',(xx,.65,.30),(.55,.50,.55),'Oak',.03);CY('Bedside lamp base',(xx,.65,.62),.13,.05,'Brass');CY('Bedside lamp stem',(xx,.65,.76),.018,.28,'Brass');CY('Bedside lamp shade',(xx,.65,.92),.17,.23,'Fabric ivory')

def cabinet(x,y,length=3,height=2.55,ma='Oak'):
 B('Cabinet carcass',(x,y,height/2),(length,.60,height),ma,.018)
 for i in range(max(2,round(length/.6))):
  xx=x-length/2+(i+.5)*length/max(2,round(length/.6));B('Cabinet front',(xx,y-.313,height/2),(length/max(2,round(length/.6))-.018,.045,height-.04),ma,.008)
  B('Cabinet pull',(xx+.12,y-.348,height*.45),(.016,.025,.30),'Charcoal metal',.005)

def kitchen(f,x,y,angle=0):
 at(f,x,y,angle);cabinet(0,1.6,5,.87)
 B('Kitchen stone counter',(0,1.6,.92),(5.08,.69,.09),'Limestone',.02)
 cabinet(-2.7,1.6,.9,2.55);B('Oven glass',(-2.7,1.26,1.42),(.64,.045,.56),'Black screen',.01)
 B('Induction hob',(-.6,1.56,.973),(.85,.48,.025),'Black screen',.01)
 B('Sink rim',(1.3,1.55,.975),(.67,.44,.025),'Charcoal metal',.03);B('Sink basin',(1.3,1.55,.98),(.56,.34,.02),'Asphalt',.04)
 CY('Kitchen tap',(1.3,1.76,1.13),.024,.34,'Brass')
 B('Island base',(0,-.25,.43),(3.6,1.1,.86),'Oak',.025);B('Island stone top',(0,-.32,.92),(3.85,1.40,.10),'Limestone',.035)
 for xx in [-1.15,0,1.15]:
  CY('Bar stool seat',(xx,-1.48,.69),.25,.11,'Fabric ivory');CY('Bar stool pedestal',(xx,-1.48,.34),.032,.68);CY('Bar stool foot',(xx,-1.48,.035),.24,.055)

def bath(f,x,y,angle=0,tub=True):
 at(f,x,y,angle);B('Bathroom vanity',(0,0,.44),(1.6,.56,.82),'Oak',.02);B('Vanity top',(0,0,.89),(1.65,.59,.08),'Limestone',.02)
 for xx in [-.42,.42]:
  B('Washbasin',(xx,-.02,.97),(.48,.34,.13),'Porcelain',.075);CY('Faucet',(xx,.20,1.09),.022,.27,'Brass')
 B('Mirror',(0,.3,1.66),(1.52,.024,1.02),'Clear glazing',.01)
 B('WC pedestal',(1.25,-1.2,.23),(.35,.56,.46),'Porcelain',.09);B('WC pan',(1.25,-1.2,.48),(.41,.64,.15),'Porcelain',.10);B('WC cistern',(1.25,-.95,.71),(.42,.18,.49),'Porcelain',.04)
 if tub:
  B('Tub outer shell',(-1.5,-1.6,.32),(.90,1.75,.64),'Porcelain',.17);B('Tub inner water',(-1.5,-1.6,.655),(.66,1.42,.018),'Water',.10)
 B('Shower tray',(-1.4,.9,.055),(1.15,1.1,.11),'Limestone',.018);B('Shower glass',(-.80,.9,1.1),(.025,1.12,2.2),'Clear glazing',.003)

def shelf(x=0,y=0,length=3):
 for zz in [.14,.60,1.06,1.52,1.98,2.44]:B('Bookcase shelf',(x,y,zz),(length,.35,.055),'Oak',.009)
 for xx in [-length/2,0,length/2]:B('Bookcase upright',(x+xx,y,1.3),(.05,.35,2.6),'Oak',.008)
 for z in [.8,1.26,1.72,2.18]:
  for i in range(12):
   xx=x-length/2+.15+i*(length-.3)/12;B('Book',(xx,y-.03,z),(.05+random.random()*.04,.24,.25+random.random()*.08),random.choice(['Paper','Fabric grey','Limestone']),.002)

def office(f,x,y,angle=0):
 at(f,x,y,angle);B('Office desk',(0,0,.76),(2.1,.85,.075),'Oak',.025)
 for xx in [-.85,.85]:B('Desk leg',(xx,0,.37),(.075,.65,.74),'Charcoal metal',.012)
 chair(0,.72);B('Laptop keyboard',(0,0,.812),(.41,.3,.024),'Charcoal metal',.005);B('Laptop display',(0,.16,.96),(.41,.025,.29),'Black screen',.006)
 shelf(0,1.8,3.2)

def lounger(f,x,y,angle=0):
 at(f,x,y,angle);B('Lounger timber deck',(0,0,.30),(.75,1.95,.12),'Oak',.04);B('Lounger cushion',(0,-.20,.40),(.69,1.43,.14),'Fabric ivory',.065)
 o=B('Lounger raised back',(0,.69,.55),(.69,.61,.15),'Fabric ivory',.05);o.rotation_euler.x=math.radians(24)
 for xx in [-.28,.28]:
  for yy in [-.72,.72]:B('Lounger foot',(xx,yy,.14),(.05,.05,.28),'Charcoal metal',.009)

def plant(f,x,y,height=1.4,site=False):
 global CUR
 at(f,x,y)
 if site:CUR=land
 p=O.copy();cyl('Limestone planter',p+Vector((0,0,.27)),.36,.54,'Limestone')
 cyl('Plant trunk',p+Vector((0,0,.5+height*.32)),.035,height*.65,'Bark')
 for i in range(13):
  a=i*2.4;r=.20+.20*random.random();loc=p+Vector((r*cos(a),r*sin(a),.7+height*(.2+.50*random.random())))
  ball('Olive foliage',loc,(.25,.22,.36),random.choice(['Leaves','Leaves light']))

# V2 furniture and material library, preserving the original architectural coordinate system.
exec(compile(open(os.path.join(ROOT,'details_v2.py'),encoding='utf-8').read(),'details_v2.py','exec'),globals())
# Priority public rooms
living('1F',1050,513,0);living('1F',838,384,90);living('1F',1293,568,90)
at('1F',903,534,90);table(length=3.8)
at('1F',876,273,0);table(length=3.8,outdoor=True)
living('1F',755,273,90)
kitchen('1F',774,501,90);at('1F',777,599,90);table(length=2.6)
kitchen('1F',772,787,0);office('1F',978,677,0)
at('1F',1320,478,0);cabinet(0,0,2.6,.92);B('Pool bar counter',(0,-.1,.99),(2.9,.8,.08),'Limestone')
for xx in [-.8,0,.8]:chair(xx,-.9,180)
# Main bedroom and dressing suites
bed('2F',851,390,0);small_living('2F',884,478,90)
at('2F',867,361);cabinet(0,0,3.0,2.55)
at('2F',870,572);cabinet(0,2.05,3.8);cabinet(0,-2.05,3.8);B('Dressing island',(0,0,.47),(1.7,.86,.94),'Oak')
at('2F',864,678);cabinet(0,2.0,4);cabinet(0,-1.9,4)
bath('2F',742,613,90,True)
# Repeatable bedrooms with ordinary human dimensions
for f,x,y,ang in [('1F',1344,673,0),('1F',1345,929,0),('2F',1270,532,0),('2F',1341,659,0),('2F',1340,932,0),('B1',1358,510,0),('B1',1415,855,0),('B1',1390,963,0)]:
 bed(f,x,y,ang);at(f,x+31,y+26,90);cabinet(0,0,2.4)
for y in [773,843,915,987]:
 bed('2F',876,y,90,True);at('2F',905,y-22,0);cabinet(0,0,1.6,2.35)
for f,x,y in [('1F',1385,767),('1F',1385,840),('2F',1178,484),('2F',1385,769),('2F',1385,842),('B1',1452,767),('B1',1452,1056)]:bath(f,x,y,0,False)
# terrace furniture is sparse and circulation stays clear
for x,y in [(992,365),(1050,365),(1108,365),(1166,365)]:lounger('1F',x,y,90)
for x,y in [(742,313),(796,313),(850,313)]:lounger('2F',x,y,90)
for f,x,y in [('1F',1000,411),('1F',1220,371),('1F',1380,612),('1F',990,757),('1F',1200,1018),('2F',746,416),('2F',1349,457),('2F',1413,1000)]:plant(f,x,y)
living('3F',1017,657,90);office('3F',1103,676,0)
# B1 specialist furnishings
at('B1',904,245,0);B('Ping-pong top',(0,0,.76),(1.525,2.74,.04),'Pool table felt',.012)
for xx in [-.55,.55]:
 for yy in [-.9,.9]:B('Ping-pong leg',(xx,yy,.37),(.04,.04,.74),'Charcoal metal',.004)
B('Ping-pong net',(0,0,.855),(1.68,.02,.152),'Fabric grey',.003)
for xx in [-.75,.75]:B('Ping-pong side stripe',(xx,0,.784),(.018,2.70,.004),'Porcelain',.001)
B('Ping-pong centre stripe',(0,0,.784),(.015,2.7,.004),'Porcelain',.001)
# yoga mats
at('B1',995,233)
for yy in [-2.4,0,2.4]:
 B('Yoga mat',(0,yy,.014),(.66,1.85,.025),'Fabric grey',.045);CY('Yoga bolster',(0,yy+.70,.12),.12,.25,'Fabric ivory')
# bowling runs across the reference long horizontal room, two compact lanes
at('B1',1144,386,90)
for xx in [-1.03,1.03]:
 B('Bowling lane',(xx,0,.06),(1.05,16.9,.12),'Oak',.01)
 for gx in [-.60,.60]:B('Bowling gutter',(xx+gx,0,.08),(.16,16.9,.13),'Charcoal metal',.025)
 for row in range(4):
  for j in range(row+1):
   px=xx+(j-row/2)*.21;py=7.2+row*.20
   CY('Bowling pin body',(px,py,.24),.065,.29,'Porcelain');CY('Bowling pin neck',(px,py,.42),.03,.14,'Porcelain');ball('Bowling pin head',V(px,py,.50),(.052,.052,.052),'Porcelain')
 B('Bowling foul line',(xx,-6.8,.127),(1.05,.025,.004),'Charcoal metal',.001)
CY('Ball return',(0,-7.5,.32),.22,.50,'Charcoal metal')
# Golf bay
at('B1',1084,494);B('Golf turf',(0,0,.018),(4.8,4.5,.035),'Turf',.01);B('Golf screen',(0,2.2,1.40),(4.5,.06,2.6),'Paper',.02)
B('Golf screen fairway',(0,2.16,.94),(4.4,.015,1.30),'Turf',.001);ball('Golf ball',V(0,-.85,.06),(.022,.022,.022),'Porcelain')
# Treadmills, dumbbells, bench and cycle; no oversized equipment
at('B1',889,484,0)
for xx in [-1.3,0,1.3]:
 B('Treadmill base',(xx,0,.15),(.82,1.9,.22),'Charcoal metal',.06);B('Treadmill belt',(xx,-.12,.277),(.59,1.48,.025),'Asphalt',.015)
 for dx in [-.32,.32]:B('Treadmill upright',(xx+dx,.66,.78),(.06,.075,1.1),'Charcoal metal',.01)
 B('Treadmill console',(xx,.68,1.35),(.66,.25,.08),'Charcoal metal',.025)
at('B1',981,510);B('Weight bench',(0,0,.52),(.46,1.3,.16),'Fabric grey',.05)
for yy in [-.45,.45]:B('Bench support',(0,yy,.23),(.48,.12,.46),'Charcoal metal',.015)
for i in range(5):
 xx=(i-2)*.43;B('Dumbbell grip',(xx,1.8,.86),(.26,.04,.04),'Charcoal metal',.009)
 for dx in [-.16,.16]:ball('Dumbbell weight',V(xx+dx,1.8,.86),(.08,.1,.1),'Charcoal metal')
B('Weight rack',(0,1.8,.54),(2.3,.46,.6),'Charcoal metal',.02)
# spa couches / sauna benches
at('B1',668,201);B('Massage couch',(0,0,.72),(.78,1.95,.2),'Fabric ivory',.08)
for xx in [-.28,.28]:B('Massage couch leg',(xx,0,.32),(.08,1.40,.64),'Oak',.015)
at('B1',666,392);B('Sauna bench',(0,0,.48),(2.8,.65,.16),'Oak',.025)
# wine bottle racks with repeated shelf units
for f in ['B1','1F']:
 at(f,1193,496)
 for xx in [-2.25,2.25]:
  B('Wine rack backing',(xx,0,1.3),(.40,5.4,2.6),'Oak',.015)
  for zz in [.35,.82,1.29,1.76,2.23]:
   B('Wine shelf',(xx,0,zz),(.55,5.4,.045),'Oak',.007)
   for i in range(12):
    yy=(i-5.5)*.4;CY('Wine bottle',(xx,yy,zz+.15),.045,.26,'Leaves');CY('Bottle neck',(xx,yy,zz+.31),.018,.08,'Brass')
 B('Wine tasting table',(0,0,.93),(1.3,1.7,.09),'Limestone',.03);B('Wine table base',(0,0,.44),(.3,.8,.88),'Oak')
# Cinema two rows of comfortable seats facing screen
for x,y in [(723,800),(1284,545)]:
 at('B1',x,y)
 small=(x>1200)
 B('Cinema projection wall',(0,1.6 if small else 2.7,1.48),(3.25 if small else 5.5,.10,2.35),'Black screen',.015)
 B('Cinema screen',(0,1.535 if small else 2.635,1.55),(2.85 if small else 4.6,.018,1.95),'Paper',.005)
 for yy in ([0] if small else [0,-1.6]):
  for xx in ([-.67,.67] if small else [-1.5,0,1.5]):sofa(xx,yy,.95,'Fabric grey')
living('B1',1390,672,90);living('B1',971,675,90);living('B1',674,641,90)
at('B1',745,919);B('Billiard table frame',(0,0,.69),(1.75,2.9,.30),'Oak',.08);B('Billiard felt',(0,0,.86),(1.52,2.67,.05),'Pool table felt',.02)
for xx in [-.6,.6]:
 for yy in [-1.1,1.1]:B('Billiard leg',(xx,yy,.32),(.19,.19,.64),'Oak',.03)
for i in range(7):ball('Billiard ball',V(random.uniform(-.5,.5),random.uniform(-1,1),.92),(.029,.029,.029),random.choice(['Porcelain','Brass','Fabric grey']))
# garage vehicles: a recognisable wheel/body/cabin assembly at normal 4.6 m scale
for f,positions in [('B1',[(902,810),(971,810),(1040,810),(902,965)]),('1F',[(902,830),(902,942)])]:
 for x,y in positions:
  at(f,x,y);B('Vehicle body',(0,0,.63),(1.82,4.55,.63),'Fabric grey',.24);B('Vehicle glazed cabin',(0,-.20,1.12),(1.59,2.2,.75),'Clear glazing',.26);B('Vehicle roof',(0,-.2,1.54),(1.55,1.8,.07),'Charcoal metal',.035)
  for xx in [-.85,.85]:
   for yy in [-1.42,1.42]:
    o=CY('Tyre',(xx,yy,.39),.36,.19,'Asphalt');o.rotation_euler.y=pi/2
  for xx in [-.57,.57]:B('Headlight',(xx,2.28,.68),(.39,.03,.13),'Porcelain',.025)
  B('Parking bay line',(-1.35,0,.008),(.04,5.2,.014),'Porcelain',.001);B('Parking bay stop',(0,-2.47,.07),(1.5,.14,.14),'Limestone',.015)
# Laundry and service equipment
for f,x,y in [('1F',766,913),('2F',1103,679)]:
 at(f,x,y)
 for xx in [-.40,.40]:
  B('Washing machine',(xx,0,.45),(.65,.65,.9),'Porcelain',.045);o=CY('Washer porthole',(xx,-.34,.47),.22,.03,'Black screen');o.rotation_euler.x=pi/2
 B('Laundry counter',(0,0,.94),(1.55,.72,.07),'Limestone',.02)
for x,y in [(1285,795),(1300,1055)]:
 at('B1',x,y)
 for yy in [-.8,.8]:B('MEP cabinet',(0,yy,1.05),(1.25,.75,2.1),'Fabric grey',.025)
# sparse soffit lights / ceilings at key rooms, individually switchable details
for f,points in [('1F',[(1020,472),(1080,472),(1020,566),(1080,566),(767,355),(879,355),(770,415),(879,415),(905,486),(905,581)]),('2F',[(814,364),(887,364),(850,417),(1342,627),(1342,690)]),('B1',[(903,212),(903,286),(980,382),(1140,382),(1290,382),(906,667),(1024,667)])]:
 setfloor(f,'Details')
 for x,y in points:
  high=(f=='1F' and x in [1020,1080])
  cyl('Flush ceiling downlight',P(x,y,Z+(5.995 if high else 2.845)),.095,.025,'Light warm')
# scaled paving joints confined to site edges and terrace bands
setfloor('1F','Details')
for yy in range(348,430,23):beam('Terrace paving joint',P(974,yy,Z+.005),P(1320,yy,Z+.005),.011,.009,'Limestone',0)
for yy in range(245,1055,25):beam('West paving joint',P(638,yy,Z+.005),P(696,yy,Z+.005),.012,.01,'Limestone',0)
# subtle planted landscape outside footprint, ground kept below exposed B1 windows
CUR=land;floorid='Site';Z=0
box('Quiet presentation ground',(0,0,-.48),(1600,1600,.3),'Ground',.02,col=land)
# entrance paving in front of south boundary
pb('Arrival paving',860,1095,1270,1250,-.28,.08,'Limestone')
for x,y in [(589,231),(589,667),(580,1080),(1524,823),(1567,1070),(854,1180),(1376,1160)]:plant('B1',x,y,2.4,True)
CUR=land;floorid='Site';Z=0
for x,y in [(650,1130),(824,1130),(1320,1130),(1460,1130),(1530,952),(1530,760)]:
 p=Vector(P(x,y,-.28));cyl('Bollard body',p+Vector((0,0,.38)),.06,.76,'Charcoal metal',col=land);cyl('Bollard light',p+Vector((0,0,.72)),.065,.08,'Light warm',col=land)
for f in floors:
 C[f,'Ceilings']=coll(f+' / Ceilings',floors[f])
 for o in list(C[f,'Details'].objects):
  if 'Flush ceiling downlight' in o.name:C[f,'Details'].objects.unlink(o);C[f,'Ceilings'].objects.link(o)
refine_architecture_v2()
# Scene lighting and native render cameras
scene.world=bpy.data.worlds.new('Neutral daylight sky');scene.world.use_nodes=True
n=scene.world.node_tree.nodes;l=scene.world.node_tree.links;n.clear();out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.66,.76,.89,1);bg.inputs['Strength'].default_value=.55;l.new(bg.outputs['Background'],out.inputs['Surface'])
def light(name,kind,loc,power,color,size=1,target=None):
 d=bpy.data.lights.new(name,kind);d.energy=power;d.color=color
 if kind=='AREA':d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);lightcol.objects.link(o);o.location=loc
 if target:o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 return o
sun=light('Soft late morning sun','SUN',(30,40,70),2.3,(1,.90,.75));sun.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-35));sun.data.angle=math.radians(18)
light('Large sky fill','AREA',(-20,-5,42),3800,(.73,.83,1),35,(0,0,0))
for name,pos,target in [('Living fill',P(1050,500,5.65),P(1050,500,3.5)),('Family fill',P(820,380,5.68),P(820,380,3.5)),('Master fill',P(850,380,8.85),P(850,380,6.6))]:light(name,'AREA',pos,260,(1,.88,.74),3,target)

light('Kitchen ceiling soft fill','AREA',P(779,521,5.72),360,(1,.9,.77),3,P(775,520,4.0))
light('Kitchen window bounce','AREA',P(834,485,5.2),180,(1,.94,.84),2.2,P(765,511,4.1))

def camera(name,loc,target,lens=50,ortho=None):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);camcol.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=500;d.clip_start=.05
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o
cams={}
cams['01_Aerial']=camera('01 · 参考鸟瞰 / northeast',(70,85,47),(-1,0,3),53)
cams['02_East']=camera('02 · 东侧外观',(100,31,28),(0,0,4),50)
cams['03_Courtyard']=camera('03 · 南侧双翼与中庭',(54,-75,36),(0,-3,4),48)
cams['04_Pool']=camera('04 · 无边泳池与玻璃立面',P(1465,200,10.2),P(992,427,5.1),44)
cams['08_Living']=camera('08 · 主客厅室内',P(1108,578,4.75),P(1025,475,4.35),25)
cams['09_Master']=camera('09 · 主卧室内',P(908,425,7.87),P(828,355,7.22),25)
for f in ['B1','1F','2F']:
 z={'B1':0,'1F':3.15,'2F':6.3}[f];cams['PLAN_'+f]=camera(f+' · 家具平面',(0,0,z+85),(0,0,z),50,58)
 cams['AXON_'+f]=camera(f+' · 剖切轴测',(65,80,z+94),(0,0,z),50,75)
scene.camera=cams['01_Aerial']
# Main scene labels excluded; plans can turn them on independently.
for f in floors:
 scene.view_layers[0].layer_collection.children[floors[f].name].children[C[f,'Labels'].name].exclude=True
# Separate scenes link editable source geometry, so each floor can be inspected immediately.
plan_scenes={}
for f in ['B1','1F','2F']:
 sc=bpy.data.scenes.new('10 · '+f+' 家具平面 / isolated');sc.world=scene.world;sc.collection.children.link(floors[f]);sc.collection.children.link(lightcol);sc.collection.children.link(camcol);sc.camera=cams['PLAN_'+f]
 plan_scenes[f]=sc
 # Labels retained but hidden in render by view-layer exclusion; semantic names remain in outliner.
 sc.view_layers[0].layer_collection.children[floors[f].name].children[C[f,'Labels'].name].exclude=True
 sc.view_layers[0].layer_collection.children[floors[f].name].children[C[f,'Ceilings'].name].exclude=True
for level,lower in [('1F','B1'),('2F','1F')]:
 context_col=bpy.data.collections.new(level+' plan context · lower circulation');plan_scenes[level].collection.children.link(context_col)
 for o in list(C[lower,'Structure'].objects):
  if 'Stair ' in o.name or (level=='1F' and ('半环形车辆坡道' in o.name or 'Ramp continuous guard wall' in o.name)):context_col.objects.link(o)
# Reference images are packed image empties, disabled by default. Same origin/scale for all plans.
refdir=os.path.dirname(ROOT)
for f,nm in [('B1','Image_1788710156034_576.png'),('1F','Image_1788710160156_448.png'),('2F','Image_1788710163745_824.png')]:
 imgpath=next((p for p in [os.path.join(ROOT,'references',nm),os.path.join(refdir,nm)] if os.path.exists(p)),None)
 if imgpath is None:
  print('Optional reference image missing:',nm,flush=True);continue
 im=bpy.data.images.load(imgpath);im.pack();o=bpy.data.objects.new(f+' · 原始平面图（整幅）',None);refs.objects.link(o);o.empty_display_type='IMAGE';o.data=im;o.empty_display_size=2048*S;o.location=P(1024,576,{'B1':0,'1F':3.15,'2F':6.3}[f]-.35);o.color[3]=.35;o['note']='Image display coordinates share scale 18.75px/m; original source 3840×2160.'
# V2 additional cameras and an independently lit evening scene.
cams['10_Kitchen']=camera('10 · 西厨细节',P(839,544,4.77),P(776,484,4.22),27)
cams['11_Twilight']=camera('11 · 傍晚鸟瞰',(74,79,39),(-1,0,3),54)
cams['PLAN_3F']=camera('3F · 家具平面',(0,0,94),(0,0,9.45),50,58)
cams['AXON_3F']=camera('3F · 剖切轴测',(65,80,103),(0,0,9.45),50,75)
sc=bpy.data.scenes.new('10 · 3F 家具平面 / isolated');sc.world=scene.world;sc.collection.children.link(floors['3F']);sc.collection.children.link(lightcol);sc.collection.children.link(camcol);sc.camera=cams['PLAN_3F'];plan_scenes['3F']=sc
sc.view_layers[0].layer_collection.children[floors['3F'].name].children[C['3F','Labels'].name].exclude=True
sc.view_layers[0].layer_collection.children[floors['3F'].name].children[C['3F','Ceilings'].name].exclude=True
evening_scene=bpy.data.scenes.new('20 · 完整建筑 | TWILIGHT');evening_scene.world=scene.world.copy();bg=evening_scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.18,.28,.48,1);bg.inputs['Strength'].default_value=.38
for col_ in list(floors.values())+[land,camcol]:evening_scene.collection.children.link(col_)
evening_lights=bpy.data.collections.new('Lighting · 傍晚');evening_scene.collection.children.link(evening_lights)
for original in lightcol.objects:
 obj=original.copy();obj.data=original.data.copy();evening_lights.objects.link(obj)
 if obj.data.type=='SUN':obj.data.energy=.7;obj.data.color=(.51,.64,1)
 elif 'fill' in obj.name.lower():obj.data.energy=140 if obj.data.energy<1000 else 850;obj.data.color=(1,.68,.38) if obj.data.energy<1000 else (.43,.59,1)
for f,x,y,z,power in [('1F',1050,508,5.7,180),('1F',838,384,5.7,120),('1F',1293,568,5.7,120),('2F',851,390,8.8,140),('2F',1341,659,8.8,100),('B1',795,330,2.6,130),('3F',1010,666,12.1,100)]:
 data=bpy.data.lights.new('V2 warm room glow '+f,'AREA');data.shape='DISK';data.size=2.5;data.energy=power;data.color=(1,.65,.32);obj=bpy.data.objects.new(data.name,data);evening_lights.objects.link(obj);obj.location=P(x,y,z)
evening_scene.camera=cams['11_Twilight']
for f in floors:evening_scene.view_layers[0].layer_collection.children[floors[f].name].children[C[f,'Labels'].name].exclude=True
finish_materials_v2()
# render configuration
for sc in [scene,evening_scene]+list(plan_scenes.values()):
 sc.render.engine='CYCLES';sc.cycles.samples=96;sc.cycles.use_denoising=True;sc.cycles.max_bounces=8;sc.cycles.transmission_bounces=6;sc.cycles.transparent_max_bounces=8
 sc.render.resolution_x=2400;sc.render.resolution_y=1660;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
 sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.35
 if sc in plan_scenes.values():sc.render.resolution_x=2000;sc.render.resolution_y=2000
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 available=[]
 for d in prefs.devices:d.use=True;available.append((d.name,d.type))
 for sc in [scene,evening_scene]+list(plan_scenes.values()):sc.cycles.device='GPU'
 print('RENDER DEVICES',available,flush=True)
except Exception as e:print('CPU fallback',e,flush=True)
# useful solid viewport defaults, camera view on reopening
bpy.context.window.scene=scene
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.clip_end=1000;area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.region_3d.view_perspective='CAMERA'
scene['reference_method']='All 13 source images reviewed. Unified plan coordinates 18.75 display px/m; 3.15m storeys.'
scene['materials']='Supplementary presentation design: warm plaster / limestone / oak / charcoal aluminium.'
scene['ramp_assumption']='Plan half-annulus inner radius 1.97m, outer 5.76m; 3.15m rise yields about 26% centreline slope. Geometry retained, not a construction detail.'
scene['floor_datums_m']='B1=0.00; 1F=3.15; 2F=6.30; 3F=9.45; upper roof=12.60. Slabs extend BELOW each datum.'
scene['version']='2.0'
# Embed the generation script as a text datablock too.
t=bpy.data.texts.new('DETAILS_V2 · details_v2.py');t.write(open(os.path.join(ROOT,'details_v2.py'),encoding='utf-8').read())
textblock=bpy.data.texts.new('BUILD_SCRIPT · build_villa.py');textblock.write(open(__file__,encoding='utf-8').read())
with open(os.path.join(ROOT,'room_schedule.json'),'w',encoding='utf-8') as f:json.dump(rooms,f,ensure_ascii=False,indent=2)
with open(os.path.join(ROOT,'qa','scene_manifest.json'),'w',encoding='utf-8') as f:json.dump({'objects':len(scene.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),'scenes':[s.name for s in bpy.data.scenes],'rooms':len(rooms),'bounds_m':[46.67,50.4],'storey':3.15},f,ensure_ascii=False,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Guanru_Park_2.0.blend'))
print('BUILD COMPLETE',len(scene.objects),flush=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if 'preview' in args:
 scene.render.resolution_percentage=50;scene.cycles.samples=20;scene.render.filepath=os.path.join(ROOT,'qa','01_preview.png');bpy.ops.render.render(write_still=True)
elif 'render' in args:
 for key in ['01_Aerial','02_East','03_Courtyard','04_Pool','08_Living','09_Master']:
  scene.camera=cams[key];scene.render.filepath=os.path.join(ROOT,'renders',key+'.png');bpy.ops.render.render(write_still=True,scene=scene.name)
 for i,f in enumerate(['B1','1F','2F'],5):
  sc=plan_scenes[f];sc.render.filepath=os.path.join(ROOT,'renders',f'{i:02d}_{f}_Plan.png');bpy.ops.render.render(write_still=True,scene=sc.name)
  sc.camera=cams['AXON_'+f];sc.render.filepath=os.path.join(ROOT,'renders',f'{i:02d}_{f}_Axon.png');bpy.ops.render.render(write_still=True,scene=sc.name)
 scene.camera=cams['01_Aerial'];bpy.context.window.scene=scene
 for f in plan_scenes:plan_scenes[f].camera=cams['PLAN_'+f]
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Guanru_Park_2.0.blend'))
