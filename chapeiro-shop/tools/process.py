import cv2, numpy as np, os, sys, json, re
from PIL import Image, ImageDraw, ImageFont
OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True); os.makedirs('cut',exist_ok=True)
only=set(sys.argv[2].split(',')) if len(sys.argv)>2 and sys.argv[2] else None
data=open('/home/user/githugb-tes/chapeiro-shop/data.js').read()
VIEW={m[0]:m[1] for m in re.findall(r'p\("(\w+)".*?"(frente|costas)"\)',data)}
ALL={m for m in re.findall(r'p\("(\w+)"[^\n]*allover: true',data)}
FONT='/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
NAMES=[('Preto',(28,26,28)),('Grafite',(70,68,70)),('Off-white',(232,224,210)),('Areia',(196,180,158)),
 ('Lilás',(178,152,206)),('Roxo',(80,52,110)),('Ameixa',(70,40,70)),('Malva',(160,110,130)),('Uva',(110,90,140)),
 ('Terracota',(214,104,64)),('Pêssego',(236,170,140)),('Cáqui',(170,155,130))]
def fill(keep):
    ff=(~keep).astype(np.uint8); h,w=ff.shape
    fm=np.zeros((h+2,w+2),np.uint8); cv2.floodFill(ff,fm,(0,0),2)
    return keep|(ff==1)
def largest(b):
    nl,lab,st,_=cv2.connectedComponentsWithStats(b.astype(np.uint8))
    if nl<2: return b>0
    return lab==1+np.argmax(st[1:,4])
def segment(t,m):
    P=8
    tp=cv2.copyMakeBorder(t,P,P,P,P,cv2.BORDER_REPLICATE); mp=cv2.copyMakeBorder(m,P,P,P,P,cv2.BORDER_CONSTANT,0)
    core=largest(mp>128)
    gm=np.full(mp.shape,cv2.GC_PR_BGD,np.uint8)
    gm[mp>40]=cv2.GC_PR_FGD
    gm[cv2.erode(fill(core).astype(np.uint8),np.ones((9,9),np.uint8))>0]=cv2.GC_FGD
    far=cv2.dilate((mp>40).astype(np.uint8),np.ones((25,25),np.uint8))==0
    gm[far]=cv2.GC_BGD; gm[:P]=gm[-P:]=gm[:,:P]=gm[:,-P:]=cv2.GC_BGD
    try:
        cv2.grabCut(tp,gm,None,np.zeros((1,65)),np.zeros((1,65)),5,cv2.GC_INIT_WITH_MASK)
    except cv2.error: pass
    fg=(gm==cv2.GC_FGD)|(gm==cv2.GC_PR_FGD)
    fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    keep=fill(largest(fg))[P:-P,P:-P]
    return keep
def dominant(rgb,mask):
    px=rgb[mask].reshape(-1,3).astype(np.float32)
    lab=cv2.cvtColor(px.reshape(-1,1,3).astype(np.uint8),cv2.COLOR_RGB2LAB).reshape(-1,3).astype(np.int32)
    q=(lab//12); key=q[:,0]*10000+q[:,1]*100+q[:,2]
    vals,cnt=np.unique(key,return_counts=True); best=vals[np.argmax(cnt)]
    sel=key==best
    return px[sel].mean(0)
def name(c):
    return min(NAMES,key=lambda n: sum((a-b)**2 for a,b in zip(c,n[1])))[0]
def orbit_icon(ink,acc,size):
    S=4; W,H=200*S,130*S
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.ellipse([12*S,38*S,188*S,92*S],outline=ink+(255,),width=7*S)
    import math
    a=math.radians(-55); cx,cy=100*S,65*S
    def pt(u,v): return (cx+u*math.cos(a)-v*math.sin(a), cy+u*math.sin(a)+v*math.cos(a))
    d.line([pt(-62*S,0),pt(18*S,0)],fill=acc+(255,),width=9*S)
    d.polygon([pt(18*S,-16*S),pt(58*S,-16*S),pt(58*S,16*S),pt(18*S,16*S)],fill=acc+(255,))
    for v in (-7,0,7): d.line([pt(28*S,v*S),pt(52*S,v*S)],fill=(0,0,0,0),width=3*S)
    im=im.resize((size,int(size*H/W)),Image.LANCZOS)
    return im
def synth_side(rgb,alpha,kind,allover,base):
    """Gera o lado que não aparece na prancha: espelha a silhueta e pinta o tecido com o sombreado das dobras."""
    h,w=alpha.shape; mask=alpha>127
    if allover:
        out=rgb[:,::-1].copy()
    else:
        lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32); bl=cv2.cvtColor(np.uint8([[base]]),cv2.COLOR_RGB2LAB)[0,0].astype(np.float32)
        d=np.sqrt(((lab-bl)**2*[0.3,1,1]).sum(-1))
        fabric=mask&(d<14)
        L=lab[:,:,0]
        ratio=np.where(fabric,L/max(bl[0],1),0).astype(np.float32)
        wgt=fabric.astype(np.float32)
        k=(0,0); s=max(w,h)/18
        num=cv2.GaussianBlur(ratio,k,s); den=cv2.GaussianBlur(wgt,k,s)
        sh=np.where(den>1e-3,num/np.maximum(den,1e-3),1)
        sh=np.clip(sh,0.6,1.25)
        # bordas levemente mais escuras dão volume
        dist=cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,5)
        edge=0.88+0.12*np.clip(dist/(0.06*w),0,1)
        grain=np.random.default_rng(1).normal(0,2.2,(h,w,1))
        out=np.clip(base[None,None,:]*(sh*edge)[...,None]+grain,0,255).astype(np.uint8)[:,::-1]
    m2=mask[:,::-1]
    out[~m2]=0
    img=Image.fromarray(out); dr=ImageDraw.Draw(img)
    light=sum(base)/3>140
    ink=(70,40,105) if light else (232,224,210)
    acc=(226,104,42)
    # gola: faixa mais escura acompanhando o topo central
    ys=np.argmax(m2,axis=0); cols=[x for x in range(int(w*.36),int(w*.64)) if m2[:,x].any()]
    neck_top=int(np.median([ys[x] for x in cols])) if cols else 0
    if not allover:
        for x in cols:
            y0=ys[x]; dy=6 if kind=='costas' else 0
            for y in range(y0, min(h,y0+max(3,h//60))):
                px=img.getpixel((x,y)); img.putpixel((x,y),tuple(int(c*0.82) for c in px))
    if kind=='costas':
        # assinatura nas costas, abaixo da gola
        f=ImageFont.truetype(FONT,max(9,w//22)); txt='CHAPEIRO'
        tw=dr.textlength(txt,font=f); y=neck_top+h*0.07
        dr.text(((w-tw)/2,y),txt,font=f,fill=ink)
        f2=ImageFont.truetype(FONT,max(7,w//34)); t2='303'; tw2=dr.textlength(t2,font=f2)
        dr.text(((w-tw2)/2,y+w//18),t2,font=f2,fill=acc)
    else:
        # frente gerada: ícone Chapeiro (espátula em órbita) no peito, lado esquerdo de quem veste
        icon=orbit_icon(ink,acc,int(w*0.17))
        img.paste(icon,(int(w*0.64-icon.width/2),int(neck_top+h*0.17)),icon)
    o=np.array(img)
    a=alpha[:,::-1]
    return o,a
def bleed(rgb,a):
    # estende a cor da peça para fora da silhueta, evitando franja escura na borda filtrada
    w=(a>200).astype(np.float32); acc=rgb.astype(np.float32)*w[...,None]; out=rgb.astype(np.float32).copy()
    filled=w>0
    for s in (2,4,8,16):
        num=cv2.GaussianBlur(acc,(0,0),s); den=cv2.GaussianBlur(w,(0,0),s)
        ok=(~filled)&(den>1e-4)
        out[ok]=num[ok]/den[ok,None]; filled|=ok
    out[a>200]=rgb[a>200]
    return np.clip(out,0,255).astype(np.uint8)
# correções manuais em coordenadas do recorte bruto
ERASE={'A13a':[(0,80,14,118)],'B09b':[(80,200,104,227)],'B11b':[(8,175,34,206)],'B17b':[(14,186,38,216)]}
MIRROR={'B09b':(96,45),'B11b':(127,70)}  # (centro da gola, x abaixo do qual espelha): manga coberta pela peça vizinha
def fix(code,t,m):
    t=t.copy(); m=m.copy()
    bgc=np.median(np.concatenate([t[:4].reshape(-1,3),t[-4:].reshape(-1,3)]),0)
    for x0,y0,x1,y1 in ERASE.get(code,[]):
        t[y0:y1,x0:x1]=bgc; m[y0:y1,x0:x1]=0
    if code=='A15a':  # texto da prancha encostado na manga: pinta com o preto da peça
        reg=t[88:120,0:30]; txt=reg.mean(-1)>90; reg[txt&(np.arange(30)[None,:]>8)]=(28,26,28); t[88:120,0:30]=reg
        t[88:120,0:9]=bgc; m[88:120,0:9]=0
    if code in MIRROR:
        c,lim=MIRROR[code]
        for x in range(0,lim):
            xm=2*c-x
            if xm<t.shape[1]: t[:,x]=t[:,xm]; m[:,x]=m[:,xm]
    return t,m
meta={}
for f in sorted(os.listdir('raw')):
    code=f[:-4]; P,v=code[:-1],code[-1]
    if only and code not in only: continue
    t=cv2.imread('raw/'+f); mf='m_bi/'+f if os.path.exists('m_bi/'+f) else 'm_isnet/'+f
    m=cv2.imread(mf,0)
    t,m=fix(code,t,m)
    keep=segment(t,m)
    ys,xs=np.where(keep); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    pad=4
    y0,x0=max(0,y0-pad),max(0,x0-pad); y1,x1=min(t.shape[0],y1+pad),min(t.shape[1],x1+pad)
    rgb=cv2.cvtColor(t[y0:y1,x0:x1],cv2.COLOR_BGR2RGB); k=keep[y0:y1,x0:x1]
    # upscale 2x for texture
    S=2
    rgb=cv2.resize(rgb,None,fx=S,fy=S,interpolation=cv2.INTER_LANCZOS4)
    bl=cv2.GaussianBlur(rgb,(0,0),1.2); rgb=cv2.addWeighted(rgb,1.5,bl,-0.5,0)
    am=cv2.resize(k.astype(np.uint8)*255,None,fx=S,fy=S,interpolation=cv2.INTER_LINEAR)
    am=cv2.GaussianBlur(am,(0,0),1.0); am=np.clip((am.astype(np.float32)-128)*2+128,0,255).astype(np.uint8)
    rgb[am<8]=0
    base=dominant(rgb,am>200)
    view=VIEW.get(P,'frente')
    other,oa=synth_side(rgb,am,'costas' if view=='frente' else 'frente',P in ALL,base)
    front,fa,back,ba=(rgb,am,other,oa) if view=='frente' else (other,oa,rgb,am)
    # back textures are stored as seen from behind (mirrored silhouette)
    for side,im,a in (('front',front,fa),('back',back,ba)):
        im=bleed(im,a)
        Image.fromarray(np.dstack([im,a])).save(f'{OUT}/{code}-{side}.webp',quality=86,method=6)
    cv2.imwrite(f'cut/{code}.png',cv2.cvtColor(np.dstack([rgb,am]),cv2.COLOR_RGBA2BGRA))
    meta[code]={'color':name(tuple(base)),'hex':'#%02x%02x%02x'%tuple(int(c) for c in base),'w':int(rgb.shape[1]),'h':int(rgb.shape[0])}
    print(code,meta[code]['color'],mf[:4],flush=True)
old=json.load(open(OUT+'/meta.json')) if os.path.exists(OUT+'/meta.json') else {}
old.update(meta); json.dump(old,open(OUT+'/meta.json','w'),indent=0,ensure_ascii=False)
