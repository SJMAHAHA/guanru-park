from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent/'textures';ROOT.mkdir(exist_ok=True)
N=1024;y,x=np.mgrid[0:N,0:N].astype(float)/N
rng=np.random.default_rng(47)
def noise():
 s=np.zeros((N,N))
 for freq in [2,4,8,16,32,64,128]:
  a=rng.uniform(0,6.28);b=rng.uniform(0,6.28)
  s+=np.sin(2*np.pi*freq*x+a)*np.cos(2*np.pi*freq*y+b)/freq**.7
 return s/(np.max(abs(s))+1e-6)
base=noise();fine=noise()
def save(name,color,height,rough):
 c=np.clip(color,0,1);Image.fromarray(np.uint8(c*255)).save(ROOT/(name+'_color.jpg'),quality=93)
 dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*N*.025
 dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*N*.025
 norm=np.stack([-dx,-dy,np.ones_like(dx)],axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
 Image.fromarray(np.uint8((norm*.5+.5)*255)).save(ROOT/(name+'_normal.png'))
 rr=np.clip(rough,0,1);rr=np.full((N,N),rr) if np.ndim(rr)==0 else rr
 Image.fromarray(np.uint8(rr*255)).save(ROOT/(name+'_rough.jpg'),quality=95)
colors={'limestone':np.array([.72,.70,.65]),'plaster':np.array([.86,.855,.825]),'linen':np.array([.78,.755,.695])}
veins=np.exp(-np.square(np.sin(2*np.pi*(2*x+y+.045*base)))/.006)*.025
save('limestone',colors['limestone'][None,None,:]+(base*.025-veins)[...,None],base*.03,.62+base*.045)
save('plaster',colors['plaster'][None,None,:]+fine[...,None]*.015,fine*.03,.84+fine*.035)
shift=x+.004*np.sin(2*np.pi*y)+.0015*np.sin(6*np.pi*y)
grain=.018*np.sin(2*np.pi*7*shift)+.010*np.sin(2*np.pi*31*shift)+.006*np.sin(2*np.pi*95*shift)+.003*np.sin(2*np.pi*211*shift)+base*.008
save('oak',np.array([.55,.45,.34])[None,None,:]+grain[...,None]*np.array([1,.87,.69]),grain*.025,.53+base*.025)
weave=(np.sin(2*np.pi*256*x)*np.sin(2*np.pi*256*y))*.035
save('linen',colors['linen'][None,None,:]+(weave+base*.02)[...,None],weave*.22,.92+base*.03)
save('linen_grey',(colors['linen'][None,None,:]+(weave+base*.02)[...,None])*np.array([.74,.80,.84]),weave*.22,.92+base*.03)
# One texture covers 0.6 m: eight 75 mm mosaic tiles with narrow grout.
xx=x*8;yy=y*8;edge=(np.minimum(xx%1,1-xx%1)<.025)|(np.minimum(yy%1,1-yy%1)<.025)
tones=rng.uniform(-.055,.055,(8,8));tone=tones[np.minimum((yy).astype(int),7),np.minimum((xx).astype(int),7)]
col=np.array([.27,.58,.57])[None,None,:]+tone[...,None]+base[...,None]*.016
col[edge]=[.70,.77,.74];height=np.where(edge,-.075,0)+base*.003
save('pool_mosaic',col,height,np.where(edge,.8,.29))
waves=np.sin(2*np.pi*(2*x+y))*.03+np.cos(2*np.pi*(3*y-x))*.025+base*.004
save('water',np.tile(np.array([.55,.78,.80]),(N,N,1)),waves,.16)
print('Created',len(list(ROOT.iterdir())),'seamless PBR texture files')
