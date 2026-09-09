"""V3 incremental interiors. Coordinates and structural openings remain in build_villa.py."""
REMOVED=[];KITCHEN_PARTS=[];FIXTURES=[]
_v2_bed=bed;_v2_bath=bath;_v2_living=living;_v2_small=small_living;_v2_office=office
mat('V3 warm wall panel',(.77,.75,.71),.77)
mat('V3 wet porcelain',(.67,.69,.67),.36)
mat('V3 brushed steel',(.48,.50,.51),.26,.85)
# Keep metals quiet and coordinated with charcoal hardware.
for name in ['Brass','Bronze trim']:
 p=M[name].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.12,.14,.145,1)

def remove_since(before,terms):
 for o in list(set(bpy.data.objects)-before):
  if any(k in o.name for k in terms):REMOVED.append(o.name);bpy.data.objects.remove(o,do_unlink=True)

def open_table(x,y,w=.55,d=.50,h=.56):
 B('V3 open table top',(x,y,h-.025),(w,d,.05),'Oak',.016)
 for dx in [-w*.39,w*.39]:
  for dy in [-d*.37,d*.37]:B('V3 open table leg',(x+dx,y+dy,(h-.05)/2),(.035,.035,h-.05),'Charcoal metal',.007)

def cabinet(x,y,length=3,height=2.55,ma='Oak'):
 # Calls outside the new kitchen are intentionally replaced with open garment rails.
 REMOVED.append(f'{floorid} cabinet at {tuple(round(v,2) for v in V(x,y,0))}')
 if height<1.2:return
 if not any(r['floor']==floorid and '衣帽' in r['name'] and r['reference_rect'][0]<(O.x/S+1068)<r['reference_rect'][2] and r['reference_rect'][1]<(622-O.y/S)<r['reference_rect'][3] for r in rooms):return
 length=min(length,3.5)
 for xx in [x-length/2,x+length/2]:
  tube('V3 freestanding garment upright',[V(xx,y-.22,0),V(xx,y,1.85)],.021,'Charcoal metal')
  B('V3 garment rail foot',(xx,y,.025),(.36,.65,.05),'Charcoal metal',.014)
 tube('V3 open hanging rod',[V(x-length/2,y,1.85),V(x+length/2,y,1.85)],.022,'Charcoal metal')
 for i in range(7):
  xx=x+(i-3)*length/9
  tube('V3 clothes hanger',[V(xx-.19,y,1.56),V(xx,y,1.76),V(xx+.19,y,1.56),V(xx-.19,y,1.56)],.009,'Oak')
  B('V3 hanging linen garment',(xx,y,1.25),(.27,.085,.6),'Fabric grey' if i%2 else 'Fabric ivory',.06)

def bed(f,x,y,angle=0,single=False):
 before=set(bpy.data.objects);_v2_bed(f,x,y,angle,single)
 remove_since(before,['Bedside cabinet','bedside drawer'])
 w=1.1 if single else 1.9
 for xx in [-w/2-.43,w/2+.43]:open_table(xx,.65)

def living(f,x,y,angle=0):
 before=set(bpy.data.objects);_v2_living(f,x,y,angle);remove_since(before,['Low media console'])
 for xx in [-1.2,1.2]:
  B('V3 loudspeaker',(xx,-3.28,.66),(.20,.21,1.25),'Charcoal metal',.02)
  for zz in [.38,.70,1.0]:
   o=CY('V3 speaker driver',(xx,-3.394,zz),.067,.014,'Fabric grey');o.rotation_euler.x=pi/2

def small_living(f,x,y,angle=0):
 before=set(bpy.data.objects);_v2_small(f,x,y,angle);remove_since(before,['Sitting room console']);open_table(0,-2.55,1.2,.4,.65)

def shelf(*args,**kwargs):pass

def office(f,x,y,angle=0):
 _v2_office(f,x,y,angle)
 B('V3 monitor frame',(0,-.20,1.12),(.72,.045,.44),'Charcoal metal',.012)
 B('V3 monitor image',(0,-.229,1.12),(.67,.008,.38),'Black screen',.004)
 B('V3 monitor stem',(0,-.19,.9),(.045,.045,.2),'Charcoal metal',.006)
 B('V3 monitor foot',(0,-.19,.817),(.3,.22,.024),'Charcoal metal',.008)
 tube('V3 desk task lamp',[V(.72,0,.82),V(.72,0,1.23),V(.48,0,1.35)],.014,'Charcoal metal')
 B('V3 task lamp head',(.46,0,1.35),(.22,.10,.05),'Charcoal metal',.02)
 B('V3 task lamp diffuser',(.46,0,1.322),(.18,.07,.008),'Light warm',.002)

def bath(f,x,y,angle=0,tub=True):
 # Resolve the room before laying out fixtures; narrow guest bathrooms get a single basin.
 rr=next((r for r in rooms if r['floor']==f and any(k in r['name'] for k in ['卫','淋浴']) and r['reference_rect'][0]<=x<=r['reference_rect'][2] and r['reference_rect'][1]<=y<=r['reference_rect'][3]),None)
 if rr is None:raise ValueError(f'Bathroom has no room record: {f} {x} {y}')
 x1,y1,x2,y2=rr['reference_rect'];width=(x2-x1)*S;depth=(y2-y1)*S;master='主卫' in rr['name'];narrow=width<2.7
 if master:
  at(f,x1+8,(y1+y2)/2,90);span=(y2-y1)*S;back=.34;basinx=0;basinw=1.6;shx=-3.2;shy=-.35;wc=(3.15,-.4)
 else:
  at(f,(x1+x2)/2,y1+8,0);span=width;back=.34;basinx=0 if narrow else .48;basinw=.70 if narrow else 1.4;shx=0 if narrow else -width/2+.73;shy=-(depth-1.4) if narrow else -.37;wc=(width/2-.57,-1.65)
 before=set(bpy.data.objects)
 B('V3 wall supported basin counter',(basinx,-.025,.89),(basinw,.59,.075),'Limestone',.015)
 for dx in [-basinw*.35,basinw*.35]:
  tube('V3 basin wall bracket',[V(basinx+dx,back,.54),V(basinx+dx,back,.85),V(basinx+dx,-.25,.85)],.02,'V3 brushed steel')
 B('V3 bathroom mirror',(basinx,back,1.69),(basinw,.025,1.00),'Mirror silver',.008)
 for dx in ([-.40,.40] if basinw>1.3 else [0]):
  cx=basinx+dx
  lathe('V3 hollow wash basin',[(0,0),(.10,0),(.155,.05),(.18,.115),(.17,.124),(.14,.06),(.08,.019),(0,.019)],(cx,-.04,.929),'Satin porcelain',64)
  tube('V3 basin mixer',[V(cx,.19,.95),V(cx,.19,1.19),V(cx,.12,1.24),V(cx,-.03,1.24)],.013,'V3 brushed steel')
  tube('V3 exposed basin drain',[V(cx,-.04,.94),V(cx,-.04,.56),V(cx,back,.56)],.026,'V3 brushed steel')
 # Mirror lighting is backed by the actual wall rather than an emissive floating plane.
 B('V3 mirror linear fixture',(basinx,back-.015,2.24),(basinw*.76,.06,.04),'Charcoal metal',.007)
 B('V3 mirror light lens',(basinx,back-.047,2.23),(basinw*.73,.008,.025),'Light warm',.003)
 tube('V3 bathroom towel bar',[V(basinx-basinw*.4,back,1.1),V(basinx-basinw*.4,-.32,1.1),V(basinx+basinw*.4,-.32,1.1),V(basinx+basinw*.4,back,1.1)],.012,'V3 brushed steel')
 B('V3 hand towel',(basinx,-.32,.94),(.30,.012,.28),'Fabric ivory',.01)
 # Toilet: open porcelain shell, separate seat ring, tank and flush controls.
 tx,ty=wc
 B('V3 toilet floor pedestal',(tx,ty,.19),(.30,.44,.38),'Satin porcelain',.09)
 bowl=lathe('V3 toilet open pan',[(0,.28),(.13,.28),(.23,.43),(.22,.48),(.175,.48),(.14,.36),(.08,.33),(0,.33)],(tx,ty,0),'Satin porcelain',64)
 centre=V(tx,ty,0)
 for v in bowl.data.vertices:
  rel=v.co-centre;u=Vector((-sin(A),cos(A),0));v.co+=u*rel.dot(u)*.38
 B('V3 toilet cistern',(tx,ty+.26,.66),(.42,.18,.61),'Satin porcelain',.03)
 B('V3 dual flush control',(tx,ty+.26,.973),(.09,.06,.012),'V3 brushed steel',.006)
 # Uninterrupted backing at toilet location, connected to the real side wall if away from the back wall.
 for yy in [ty+.26]:
  if not master:
   B('V3 toilet wall service rail',(width/2-.11,yy,.85),(.04,.34,.04),'V3 brushed steel',.006)
   tube('V3 toilet supply pipe',[V(tx,yy,.35),V(width/2-.10,yy,.35)],.009,'V3 brushed steel')
 # Frameless shower, sloped tray cue and visible drain; no vanity cabinet.
 B('V3 shower tray',(shx,shy,.065),(1.18,1.20,.13),'V3 wet porcelain',.016)
 B('V3 shower linear drain',(shx,shy+.48,.133),(.75,.052,.008),'V3 brushed steel',.003)
 if narrow:
  B('V3 shower screen',(shx-.29,shy+.62,1.12),(.59,.025,2.1),'Clear glazing',.002)
  B('V3 shower hinge post',(shx-.59,shy+.62,1.12),(.022,.025,2.1),'Charcoal metal',.003)
  tapy=shy-.48
 else:
  B('V3 shower screen',(shx+.61,shy,1.12),(.025,1.20,2.1),'Clear glazing',.002);tapy=back
 tube('V3 mounted shower riser',[V(shx,tapy,.95),V(shx,tapy,2.14),V(shx,tapy-.35,2.14)],.018,'V3 brushed steel')
 CY('V3 rainfall shower head',(shx,tapy-.36,2.125),.14,.025,'V3 brushed steel')
 B('V3 shower mixer plate',(shx,tapy-.01,1.10),(.23,.045,.07),'V3 brushed steel',.007)
 if master:
  # Open bath at the southern half of the long master bathroom.
  bx,by=2.3,-1.75;N=80;rings=[(.88,1.72,.08),(.95,1.8,.58),(.83,1.66,.64),(.7,1.51,.55),(.58,1.33,.15)];vs=[];fs=[]
  for w,d,z in rings:
   for i in range(N):
    a=i*2*pi/N;vs.append(V(bx+math.copysign(abs(cos(a))**.4,cos(a))*w/2,by+math.copysign(abs(sin(a))**.4,sin(a))*d/2,z))
  for j in range(len(rings)-1):
   for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
  fs.append(tuple(range((len(rings)-1)*N,len(rings)*N)));me=bpy.data.meshes.new('V3 open bath shell');me.from_pydata(vs,[],fs);ob=link(bpy.data.objects.new(f+' | V3 freestanding bathtub',me),'Satin porcelain')
  for face in me.polygons:face.use_smooth=True
  tube('V3 freestanding bath filler',[V(bx-.65,by,0),V(bx-.65,by,.9),V(bx-.3,by,.9)],.021,'V3 brushed steel')
 for o in set(bpy.data.objects)-before:o['room']=rr['name'];o['assembly']='V3 bathroom';o['cabinet_free']=True


def kitchen(f,x,y,angle=0):
 # North wall in west kitchen; solid west wall in Chinese kitchen. Original calls retained.
 west=y<700
 at(f,777 if west else 721,456 if west else 789,0 if west else 90)
 before=set(bpy.data.objects);tag='西厨' if west else '中厨';L=5.8 if west else 4.0;n=8 if west else 6;step=L/n;back=.64
 # Architectural recess surround, open appliance bays and continuous toe reveal.
 for xx in [-L/2-.06,L/2+.06]:B('V3 kitchen integration cheek',(xx,.23,1.42),(.12,.86,2.84),'Warm plaster',.006)
 B('V3 kitchen integration soffit',(0,.23,2.76),(L,.86,.16),'Warm plaster',.004)
 B('V3 kitchen backsplash',(0,.62,1.42),(L,.035,.98),'Limestone',.006)
 tall={0:'fridge',n-1:'oven'}
 for i in range(n):
  xx=-L/2+(i+.5)*step
  for dx in [-step/2+.015,step/2-.015]:B('V3 kitchen bay side',(xx+dx,.24,1.31 if i in tall else .48),(.03,.75,2.5 if i in tall else .83),'Oak',.004)
  B('V3 kitchen recessed toe',(xx,.35,.09),(step-.04,.45,.16),'Charcoal metal',.002)
  B('V3 kitchen bay bottom',(xx,.24,.18),(step-.03,.75,.035),'Oak',.002)
  if i==0:
   for zz,hh in [(.68,.97),(1.82,1.23)]:
    B('V3 integrated refrigerator door',(xx,-.157,zz),(step-.025,.065,hh),'Oak',.006)
    B('V3 refrigerator handle',(xx+step*.30,-.206,zz),(.022,.03,.45),'V3 brushed steel',.005)
   for j in range(8):B('V3 refrigerator vent',(xx,-.17,2.48+j*.012),(step-.10,.012,.006),'Charcoal metal',.001)
  elif i==n-1:
   for zz in [.50,2.20]:B('V3 kitchen tall door',(xx,-.16,zz),(step-.025,.05,.55),'Oak',.006)
   for zz,label in [(1.1,'oven'),(1.70,'steam oven')]:
    B('V3 '+label+' appliance body',(xx,.20,zz),(step-.09,.67,.55),'Charcoal metal',.012)
    B('V3 '+label+' glass door',(xx,-.151,zz-.04),(step-.12,.025,.38),'Black screen',.01)
    B('V3 '+label+' control fascia',(xx,-.17,zz+.205),(step-.12,.023,.11),'V3 brushed steel',.003)
    B('V3 '+label+' handle',(xx,-.20,zz+.12),(step-.22,.05,.026),'V3 brushed steel',.006)
    B('V3 '+label+' digital display',(xx,-.187,zz+.21),(.14,.006,.04),'Black screen',.002)
  else:
   if i==n-3:
    B('V3 integrated dishwasher',(xx,.22,.53),(step-.06,.69,.69),'V3 brushed steel',.01)
    B('V3 dishwasher front',(xx,-.155,.50),(step-.025,.05,.62),'Oak',.007)
    B('V3 dishwasher controls',(xx,-.181,.84),(step-.10,.01,.05),'Charcoal metal',.002)
   else:
    for zz,hh in [(.42,.47),(.78,.22)]:B('V3 kitchen drawer front',(xx,-.16,zz),(step-.025,.05,hh),'Oak',.007)
   B('V3 recessed drawer finger pull',(xx,-.183,.90),(step-.055,.018,.02),'Charcoal metal',.002)
 # Worktop constructed around a genuine sink opening.
 a=-L/2+step;b=L/2-step;sink=(n-2.5)*step-L/2;sw=.58
 for lo,hi in [(a,sink-sw/2),(sink+sw/2,b)]:
  if hi>lo:B('V3 stone worktop',((lo+hi)/2,.23,.96),(hi-lo,.82,.065),'Limestone',.008)
 for yy in [-.135,.59]:B('V3 sink worktop bridge',(sink,yy,.96),(sw,.095,.065),'Limestone',.006)
 B('V3 undermount sink bottom',(sink,.23,.77),(sw,.59,.028),'V3 brushed steel',.05)
 for dx in [-sw/2,sw/2]:B('V3 sink bowl side',(sink+dx,.23,.855),(.018,.59,.18),'V3 brushed steel',.005)
 for yy in [-.06,.52]:B('V3 sink bowl end',(sink,yy,.855),(sw,.018,.18),'V3 brushed steel',.005)
 tube('V3 kitchen mixer',[V(sink,.58,1),V(sink,.58,1.28),V(sink,.50,1.36),V(sink,.20,1.36),V(sink,.17,1.31)],.018,'V3 brushed steel')
 hob=a+step*.90
 B('V3 flush induction hob',(hob,.23,1.001),(.72,.49,.015),'Black screen',.009)
 for dx in [-.18,.18]:
  for yy in [.10,.37]:tube('V3 hob ring',[V(hob+dx+.08*cos(i*pi/20),yy+.08*sin(i*pi/20),1.011) for i in range(40)],.002,'Limestone',True)
 B('V3 integrated extraction hood',(hob,.27,2.03),(.92,.68,.085),'Charcoal metal',.01)
 B('V3 extraction riser',(hob,.48,2.36),(.33,.30,.60),'V3 brushed steel',.008)
 B('V3 hood task light',(hob,.09,1.98),(.70,.06,.012),'Light warm',.004)
 if west:
  B('V3 kitchen island plinth',(0,-2.5,.10),(2.85,.82,.20),'Charcoal metal',.02)
  for i in range(4):B('V3 kitchen island door',(-1.125+i*.75,-2.5,.53),(.73,1.03,.71),'Oak',.012)
  B('V3 island waterfall top',(0,-2.55,.96),(3.24,1.32,.08),'Limestone',.018)
  for xx in [-1.58,1.58]:B('V3 island waterfall side',(xx,-2.55,.48),(.08,1.32,.90),'Limestone',.012)
  for xx in [-1,0,1]:
   CY('V3 bar stool seat',(xx,-3.6,.72),.25,.12,'Fabric ivory')
   for dx,dy in [(-.17,-.17),(-.17,.17),(.17,-.17),(.17,.17)]:B('V3 stool leg',(xx+dx,-3.6+dy,.34),(.035,.035,.68),'Charcoal metal',.005)
   tube('V3 pendant cable',[V(xx,-2.5,2.81),V(xx,-2.5,2.13)],.004,'Charcoal metal')
   lathe('V3 pendant shade',[(.05,2.15),(.17,1.99),(.16,1.98),(.045,2.14)],(xx,-2.5,0),'Charcoal metal')
   CY('V3 pendant lens',(xx,-2.5,1.985),.14,.012,'Light warm')
 for o in set(bpy.data.objects)-before:o['room']=tag;o['kitchen_exception']=True
 KITCHEN_PARTS.append({'room':tag,'objects':len(set(bpy.data.objects)-before),'appliances':['integrated fridge','oven','steam oven','dishwasher','induction','extractor','undermount sink']})


def finish_rooms_v3():
 global CUR
 # Retire remaining legacy solids and decorative remnants, never equipment housings.
 for o in list(scene.objects):
  if any(k in o.name for k in ['Dressing island','Wine rack backing','V2 bedside drawer','Kitchen pendant','V2 pendant diffuser']):
   REMOVED.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 # Dedicated open wine rack uprights and open bar counter support.
 for f in ['B1','1F']:
  at(f,1193,496)
  for xx in [-2.25,2.25]:
   for yy in [-2.62,2.62]:B('V3 open wine rack post',(xx,yy,1.3),(.035,.035,2.6),'Charcoal metal',.006)
 at('1F',1320,478)
 for xx in [-1.15,1.15]:
  for yy in [-.35,.15]:B('V3 pool bar table leg',(xx,yy,.49),(.055,.055,.98),'Charcoal metal',.007)
 for f,y in [('2F',572),('2F',678)]:at(f,870,y);open_table(0,0,1.25,.5,.46)
 # All previously unlisted accessible upper rooms and circulation.
 extras=[('3F','屋顶起居室',(960,586,1070,730)),('3F','屋顶办公室',(1070,622,1142,730)),('3F','屋顶楼梯厅',(1142,586,1252,730)),('1F','西楼梯厅',(746,658,850,730)),('1F','东楼梯厅',(1142,622,1252,730)),('2F','西侧交通厅',(708,440,816,514)),('2F','西楼梯厅',(708,954,816,1022)),('2F','东楼梯厅',(1148,628,1246,730))]
 for f,name,r in extras:
  rooms.append({'floor':f,'name':name,'reference_rect':r,'approx_area_m2':round((r[2]-r[0])*(r[3]-r[1])*S*S,2)})
 # Missing service functions.
 bath('B1',669,545,90,False);bath('B1',1362,392,0,False)
 at('2F',758,868);table(length=2.2);office('2F',742,804,0)
 at('B1',666,392)
 for xx in [-1.1,1.1]:B('V3 sauna bench support',(xx,0,.22),(.08,.52,.44),'Oak',.009)
 B('V3 sauna heater',(0,1.0,.42),(.48,.4,.78),'Charcoal metal',.025)
 for f,x,y in [('1F',766,913),('2F',1103,679)]:
  at(f,x,y)
  for xx,label in [(-.40,'washer'),(.40,'dryer')]:
   B('V3 '+label+' control strip',(xx,-.335,.78),(.54,.018,.10),'V3 brushed steel',.007)
   o=CY('V3 '+label+' programme dial',(xx-.17,-.36,.79),.026,.02,'Charcoal metal');o.rotation_euler.x=pi/2
   B('V3 '+label+' display',(xx+.09,-.35,.79),(.16,.008,.045),'Black screen',.003)
   B('V3 '+label+' door handle',(xx+.16,-.38,.47),(.033,.04,.16),'V3 brushed steel',.01)
  for xx in [-.71,.71]:B('V3 laundry worktop leg',(xx,0,.45),(.035,.035,.9),'Charcoal metal',.005)
  lathe('V3 laundry basket',[(.22,0),(.26,.5),(.24,.52),(.20,.025)],(1.22,0,0),'Fabric ivory')
 # Floor finishes must retain pool and stair apertures (legacy room rectangles covered them).
 holes={'B1':[rect(758,167,834,407),rect(643,274,691,320)],'1F':[rect(746,658,812,730),rect(708,950,778,1022),rect(1148,628,1246,728)],'2F':[rect(710,954,778,1020),rect(1148,628,1246,728)],'3F':[rect(1162,640,1224,726)]}
 for o in list(scene.objects):
  if o.type=='MESH' and 'floor finish' in o.name:
   f=next(c.name.split(' / ')[0] for c in o.users_collection if ' / ' in c.name);setfloor(f,'Details')
   for hole in holes.get(f,[]):cut(o,hole,Z-.1,.4)
 # Finish actual wall faces, keeping existing door openings and transparent facades.
 originals=list(scene.objects)
 bpy.context.view_layer.update()
 for o in originals:
  if o.type!='MESH' or not any(k in o.name for k in ['Partition','Opaque facade']):continue
  f=next((c.name.split(' / ')[0] for c in o.users_collection if ' / ' in c.name),None)
  if f not in ['B1','1F','2F','3F']:continue
  setfloor(f,'Details');dims=Vector(tuple(max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in range(3)))
  for sign in [-1,1]:
   pt=o.matrix_world@Vector((0,sign*(dims.y/2+.008),0));rx=pt.x/S+1068;ry=622-pt.y/S
   rr=next((r for r in rooms if r['floor']==f and r['reference_rect'][0]-3<=rx<=r['reference_rect'][2]+3 and r['reference_rect'][1]-3<=ry<=r['reference_rect'][3]+3),None)
   wet=rr and any(k in rr['name'] for k in ['卫','淋浴','SPA','泡池'])
   q=box('V3 '+(rr['name'] if rr else '交通')+' wall lining',pt,(max(.02,dims.x-.02),.016,max(.05,dims.z-.03)),'V3 wet porcelain' if wet else 'V3 warm wall panel',.003);q.rotation_euler=o.rotation_euler
 # Ceiling panels and real downlights for every main room; don't cap double-height void midway.
 for idx,r in enumerate(rooms):
  f=r['floor'];name=r['name'];x1,y1,x2,y2=r['reference_rect'];cx=(x1+x2)/2;cy=(y1+y2)/2;setfloor(f,'Ceilings')
  outdoor='户外' in name;double=f=='1F' and name=='主客厅';height=5.94 if double else 2.84
  if not outdoor:
   cap=pb('V3 '+name+' finished ceiling',x1+2,y1+2,x2-2,y2-2,Z+height,.045,'Warm plaster',.004)
   if '楼梯' in name:
    for h in holes.get(f,[]):cut(cap,h,Z+height-.1,.3)
   # One or two compact rows, proportionate to area and ceiling height.
   nx=2 if x2-x1>95 else 1;ny=2 if y2-y1>110 else 1
   if '楼梯' in name:nx=ny=1
   for i in range(nx):
    for j in range(ny):
     xx=x1+(i+.5)*(x2-x1)/nx;yy=y1+(j+.5)*(y2-y1)/ny
     if '楼梯' in name:xx=x2-9;yy=y1+10
     p=P(xx,yy,Z+height-.04);cyl('V3 '+name+' recessed downlight trim',p,.095,.025,'Charcoal metal',48)
     cyl('V3 '+name+' downlight lens',(p[0],p[1],p[2]-.019),.074,.008,'Light warm',48)
     d=bpy.data.lights.new('V3 '+name+' downlight','AREA');d.energy=35 if not double else 85;d.shape='DISK';d.size=.18;d.color=(1,.83,.65);o=bpy.data.objects.new(d.name,d);lightcol.objects.link(o);o.location=(p[0],p[1],p[2]-.025)
     FIXTURES.append({'floor':f,'room':name,'position':[p[0],p[2]-.025,-p[1]],'power':d.energy,'range':5 if not double else 9})
   setfloor(f,'Details')
   # Grilles and wiring accessories mounted beside actual walls instead of freestanding in rooms.
   candidates=[o for o in originals if o.type=='MESH' and 'Partition' in o.name and any(c.name.startswith(f+' / ') for c in o.users_collection) and x1-4<=o.location.x/S+1068<=x2+4 and y1-4<=622-o.location.y/S<=y2+4 and o.dimensions.x>.8]
   if candidates:
    wall_=min(candidates,key=lambda o:(o.location-Vector(P(cx,cy,Z+1.4))).length);mx=wall_.matrix_world.copy();sgn=1 if (mx.inverted()@Vector(P(cx,cy,Z+1.4))).y>0 else -1
    for label,zz,w,h in [('switch',1.15,.09,.09),('socket',.32,.13,.08),('air grille',2.52,min(1.2,wall_.dimensions.x*.6),.14)]:
     p=mx@Vector((0,sgn*(wall_.dimensions.y/2+.025),zz-wall_.location.z+Z));q=box('V3 '+name+' '+label,p,(w,.018,h),'Porcelain' if label!='air grille' else 'Charcoal metal',.004);q.rotation_euler=wall_.rotation_euler
     if label=='socket':
      for dx in [-.026,.026]:
       a=mx@Vector((dx,sgn*(wall_.dimensions.y/2+.037),zz-wall_.location.z+Z));q=box('V3 socket aperture',a,(.008,.007,.025),'Charcoal metal',.001);q.rotation_euler=wall_.rotation_euler
   # Folded linen curtains placed at real glazing endpoints in living/sleeping rooms.
   windows=[o for o in originals if o.type=='MESH' and 'Double glazing' in o.name and any(c.name.startswith(f+' / ') for c in o.users_collection) and x1-3<=o.location.x/S+1068<=x2+3 and y1-3<=622-o.location.y/S<=y2+3]
   if windows and any(k in name for k in ['卧','宿舍','客厅','起居','办公室']):
    for o in [windows[0],windows[-1]]:
     at(f,o.location.x/S+1068,622-o.location.y/S,math.degrees(o.rotation_euler.z));CUR=C[f,'Furniture'];vs=[];fs=[]
     for j in range(13):
      for i in range(25):vs.append(V((i/24-.5)*.42,.08*cos(i/24*8*pi),.06+j/12*2.65))
     for j in range(12):
      for i in range(24):k=j*25+i;fs.append((k,k+1,k+26,k+25))
     me=bpy.data.meshes.new('V3 linen curtain');me.from_pydata(vs,[],fs);oo=link(bpy.data.objects.new(f+' | V3 '+name+' curtain',me),'Fabric ivory')
     for face in me.polygons:face.use_smooth=True
     tube('V3 curtain suspension',[V(-.25,0,2.77),V(.25,0,2.77)],.015,'Charcoal metal')
  r['finish_scope']=['地面','墙面','顶面与灯具','门套与收口','开关插座与风口'] if not outdoor else ['铺地','户外家具','照明']
  r['cabinet_policy']='厨房一体化橱柜' if '厨' in name else '无储物柜体'
  r['review']='待 Blender 与浏览器检查'
 # Persist auditable semantic inventories before mesh merging.
 (Path(ROOT)/'qa/cabinet_replacements.json').write_text(json.dumps({'removed_or_replaced':REMOVED,'kitchens':KITCHEN_PARTS},ensure_ascii=False,indent=2))
 (Path(ROOT)/'web_export/lights.json').write_text(json.dumps(FIXTURES,ensure_ascii=False,indent=2))
 t=bpy.data.texts.new('DETAILS_V3 · details_v3.py');t.write(Path(ROOT,'details_v3.py').read_text())
 print('V3 completed',len(rooms),'room records;',len(FIXTURES),'light fixtures',flush=True)
