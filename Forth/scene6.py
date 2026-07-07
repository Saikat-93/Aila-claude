#!/usr/bin/env python3
"""
Aila Launch Film — Scene 6 v2: personalized-journey hero (6.5s).
Corrections per sample (0619_2_.mp4):
  * TRANSITION: camera zooms INTO the detail card's hero photo (slow creep,
    then fast push to full-bleed) crossfading into the Paris background.
  * TEXT: warm cream (252,247,240), Lora ~86px, sample's two-beat build:
    block A first, pause, then block B + spinner together. Paragraph gap.
  * SPINNER: Aila comet ring (spinning, 1 rot/sec) below the text at left.

Text:
  A: This journey is crafted just for you.
  B: Every destination, stay, and experience
     is personalized to match your
     travel style, budget, and interests.

Assets: bg/paris.png, slices/detail_card.png, fonts/Lora.ttf
4K 3840x2160 @ 30fps.  Run:  python scene6.py aila_scene_06.mp4
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S      = 1.5
W, H   = int(2560*S), int(1440*S)
FPS    = 30
DUR    = 6.5
N      = int(DUR*FPS)

BEIGE   = (239, 233, 223)
CREAM   = (252, 247, 240)     # sample-measured text color
ORANGE  = (245, 166, 35)
BLUE    = (33, 150, 243)

AD = "./slices"
GD = "./bg"
FD = "./fonts"

FONT = ImageFont.truetype(f"{FD}/Lora.ttf", int(86*S))
try: FONT.set_variation_by_axes([500])   # sample serif weight
except Exception: pass

BLOCK_A = ["This journey is crafted just for you."]
BLOCK_B = ["Every destination, stay, and experience",
           "is personalized to match your",
           "travel style, budget, and interests."]

TEXT_X   = int(317*S)
Y_A      = int(376*S)
LINE_H   = int(122*S)
PARA_GAP = int(41*S)          # sample: 163 vs 122 line pitch
RING_C   = (int(378*S), int(1030*S))
RING_R   = 55*S

# hero photo rect on screen (measured from detail slice placement)
HERO = (int(285*S), int(215*S), int(1233*S), int(742*S))

# timeline (s)
T_CREEP  = (0.00, 0.68)       # subtle pre-zoom (sample: slow creep 0.2-0.7)
T_ZOOM   = (0.68, 1.15)       # fast push into hero photo (sample: 0.7-1.15)
XFADE_AT = 0.55               # bg crossfade begins at this zoom progress
T_WORDS_A = (1.30, 1.85)
T_LEAD_B  = 1.95              # first word of block B appears early, then pause
T_WORDS_B = (2.90, 3.55)
T_RING    = 3.35
KB        = (1.060, 1.000)    # bg settles from zoomed, continuing the push

clamp = lambda x,a=0,b=1: max(a,min(b,x))
eoc = lambda t: 1-(1-clamp(t))**3
eic = lambda t: clamp(t)**3
eio = lambda t: (lambda u: u*u*(3-2*u))(clamp(t))
lerp = lambda a,b,t: a+(b-a)*t
def lerpc(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))

# ---------- background master (scrim baked) ----------
def build_bg():
    src = Image.open(f"{GD}/paris.png").convert("RGB")
    s = max(W/src.width, H/src.height) * KB[0]
    mw, mh = int(src.width*s), int(src.height*s)
    m = src.resize((mw, mh), Image.LANCZOS)
    m = m.filter(ImageFilter.UnsharpMask(radius=2.2, percent=68, threshold=2))
    grad = Image.new("L", (mw, 1))
    for x in range(mw):
        f = x/mw
        v = int(118*max(0.0, 1.0-f*1.28) + 30)      # scrim reaches ~78% width
        grad.putpixel((x,0), v)
    scrim = grad.resize((mw, mh))
    dark = Image.new("RGB", (mw, mh), (8, 9, 12))
    return Image.composite(dark, m, scrim)
MASTER = build_bg()
MW, MH = MASTER.size

def bg_frame(t):
    z = lerp(KB[0], KB[1], eio((t-T_ZOOM[0])/(DUR-T_ZOOM[0])))
    cw, ch = int(W*KB[0]/z), int(H*KB[0]/z)
    cx, cy = MW//2, MH//2
    return MASTER.crop((cx-cw//2, cy-ch//2, cx-cw//2+cw, cy-ch//2+ch)).resize((W,H), Image.LANCZOS)

# ---------- scene-5 end state ----------
def build_prev():
    lay = Image.new("RGBA", (W, H), BEIGE+(255,))
    det = Image.open(f"{AD}/detail_card.png").convert("RGBA")
    det = det.resize((int(det.width*S), int(det.height*S)), Image.LANCZOS)
    blur = int(26*S)
    sh = Image.new("RGBA", (det.width+blur*6, det.height+blur*6), (0,0,0,0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [blur*3,blur*3,blur*3+det.width,blur*3+det.height],
        radius=int(28*S), fill=(30,26,20,54))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    px, py = int(228*S), int(158*S)
    lay.alpha_composite(sh, (px-blur*3, py-blur*3+int(18*S)))
    lay.alpha_composite(det, (px, py))
    return lay.convert("RGB")
PREV = build_prev()

HX0,HY0,HX1,HY1 = HERO
HCX, HCY = (HX0+HX1)/2, (HY0+HY1)/2
F_MAX = max(W/(HX1-HX0), H/(HY1-HY0))   # ~2.73

def zoomed_prev(s, prog):
    """camera zoom: scale s about hero center gliding toward screen center"""
    tx = lerp(HCX, W/2, prog)
    ty = lerp(HCY, H/2, prog)
    offx = tx - HCX*s
    offy = ty - HCY*s
    x0 = (0-offx)/s; y0 = (0-offy)/s
    x1 = (W-offx)/s; y1 = (H-offy)/s
    return PREV.crop((int(x0),int(y0),int(x1),int(y1))).resize((W,H), Image.LANCZOS)

# ---------- comet ring ----------
def draw_ring(img, cx, cy, R, t, alpha):
    if alpha<=0: return
    ov=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    head=(t*2*math.pi)%(2*math.pi); TRAIL=math.radians(300); STEPS=56
    for i in range(STEPS):
        f=i/(STEPS-1); ang=head-TRAIL*(1-f)
        x,y=cx+R*math.cos(ang),cy+R*math.sin(ang)
        col=lerpc(BLUE,ORANGE,f); a=int(255*(f**1.6)*alpha)
        rr=R*0.055+(R*0.16-R*0.055)*(f**1.4)
        d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col+(a,))
    hx,hy=cx+R*math.cos(head),cy+R*math.sin(head)
    hr=R*0.185
    d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=ORANGE+(int(255*alpha),))
    ov=ov.filter(ImageFilter.GaussianBlur(0.6*S))
    img.alpha_composite(ov)

# ---------- word layout ----------
_tmp=Image.new("RGB",(8,8)); _M=ImageDraw.Draw(_tmp)
def layout():
    words=[]
    space=_M.textlength(" ",font=FONT)
    y=Y_A
    for ln in BLOCK_A:
        x=TEXT_X
        for w in ln.split(" "):
            words.append(("A",w,x,y)); x+=_M.textlength(w,font=FONT)+space
        y+=LINE_H
    y+=PARA_GAP
    for ln in BLOCK_B:
        x=TEXT_X
        for w in ln.split(" "):
            words.append(("B",w,x,y)); x+=_M.textlength(w,font=FONT)+space
        y+=LINE_H
    return words
WORDS=layout()
NA=sum(1 for k,*_ in WORDS if k=="A")
NB=len(WORDS)-NA

def render_frame(i):
    t=i/FPS

    # ---------- background / transition ----------
    if t < T_ZOOM[0]:
        s=lerp(1.0,1.045,eio((t-T_CREEP[0])/(T_CREEP[1]-T_CREEP[0])))
        img=zoomed_prev(s,0.0).convert("RGBA")
    elif t < T_ZOOM[1]:
        p=eio((t-T_ZOOM[0])/(T_ZOOM[1]-T_ZOOM[0]))
        s=lerp(1.045,F_MAX,p)
        img=zoomed_prev(s,p).convert("RGBA")
        if p>XFADE_AT:
            xa=eio((p-XFADE_AT)/(1-XFADE_AT))
            bgf=bg_frame(t).convert("RGBA")
            bgf.putalpha(Image.new("L",(W,H),int(255*xa)))
            img.alpha_composite(bgf)
    else:
        img=bg_frame(t).convert("RGBA")

    # ---------- text: two beats ----------
    if t>=T_WORDS_A[0]-0.05:
        layer=Image.new("RGBA",(W,H),(0,0,0,0))
        ld=ImageDraw.Draw(layer)
        perA=(T_WORDS_A[1]-T_WORDS_A[0])/max(NA,1)
        perB=(T_WORDS_B[1]-T_WORDS_B[0])/max(NB,1)
        ja=jb=0
        for kind,w,x,y in WORDS:
            if kind=="A":
                t_on=T_WORDS_A[0]+ja*perA; ja+=1
            else:
                if jb==0: t_on=T_LEAD_B          # streaming lead word
                else:     t_on=T_WORDS_B[0]+(jb-1)*perB
                jb+=1
            a=eoc((t-t_on)/0.16)
            if a<=0: continue
            rise=int((1-a)*12*S)
            ld.text((x+int(2*S),y+rise+int(4*S)),w,font=FONT,fill=(0,0,0,int(96*a)))
            ld.text((x,y+rise),w,font=FONT,fill=CREAM+(int(255*a),))
        img.alpha_composite(layer)

    # ---------- spinning ring ----------
    if t>=T_RING:
        ra=eoc((t-T_RING)/0.30)
        draw_ring(img,RING_C[0],RING_C[1],RING_R,t,ra)

    return img.convert("RGB")

def main():
    out=sys.argv[1] if len(sys.argv)>1 else "aila_scene_06_4k.mp4"
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
         "-r",str(FPS),"-i","-","-c:v","libx264","-preset","medium","-crf","16",
         "-pix_fmt","yuv420p","-movflags","+faststart",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for i in range(N):
        p.stdin.write(render_frame(i).tobytes())
        if i%30==0: print(f"frame {i}/{N}",flush=True)
    p.stdin.close(); p.wait()
    print("done:",out)

if __name__=="__main__":
    main()
