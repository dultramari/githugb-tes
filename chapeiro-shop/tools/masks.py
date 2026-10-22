import cv2, numpy as np, os, sys
from rembg import remove, new_session
from layout import L
model=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True); os.makedirs('raw',exist_ok=True)
only=set(sys.argv[3].split(',')) if len(sys.argv)>3 else None
s=new_session(model)
for sheet,cells in L.items():
    im=cv2.imread(sheet+'.png')
    for code,x0,x1,y0,y1 in cells:
        mid=(x0+x1)//2
        for v,(a,b) in (('a',(x0,mid+8)),('b',(mid-8,x1))):
            f=f'{out}/{code}{v}.png'
            if os.path.exists(f) or (only and code+v not in only): continue
            t=im[y0:y1,a:b]; cv2.imwrite(f'raw/{code}{v}.png',t)
            p=24; tp=cv2.copyMakeBorder(t,p,p,p,p,cv2.BORDER_REPLICATE)
            m=remove(tp,session=s,only_mask=True)
            m=np.array(m)[p:-p,p:-p]
            cv2.imwrite(f,m); print(code+v,flush=True)
