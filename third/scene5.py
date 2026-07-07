#!/usr/bin/env python3
"""
Aila Launch Film — Scene 5 v2: "Aila Stay" results -> selected stay detail.
Fixes: perfectly masked card/detail cuts (rounded alpha, rebuilt shadows),
spinning pill ring, polished easing throughout.

Motion map (7.1s):
  0.00-0.20  A. icon holds centered (300px @ 1280,720) - seamless from scene 4
  0.20-0.85  icon glides up-left to the header, shrinking; crossfades out as
             the chrome (header+title+subtitle) fades in
  1.00-1.75  three property cards cascade in (rise 90px + fade, staggered)
  2.30-2.80  "AILA auto-selects best fit" pill fades in below the grid
             (comet ring spinning at 1 rot/sec)
  4.50-5.20  soft azure pulse on card 1 (the auto-selected stay)
  5.20-5.78  card 1 expands into the detail card rect, crossfading
  5.78-6.40  gentle settle (1.010 -> 1.000), then hold

Assets next to this script:
  slices/chrome.png, slices/card1..3.png, slices/detail_card.png
  fonts/Inter.ttf
4K 3840x2160 @ 30fps.  Run:  python scene5.py aila_scene_05.mp4
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S      = 1.5
W, H   = int(2560*S), int(1440*S)
FPS    = 30
DUR    = 7.1
N      = int(DUR*FPS)

BG      = (239, 233, 223)
INK     = (20, 18, 14)
ICONBLU = (10, 110, 158)      # #0A6E9E
AZURE   = (36, 147, 214)      # #2493D6
ORANGE  = (245, 166, 35)
BLUE    = (33, 150, 243)

AD = "./slices"
FD = "./fonts"

def load(p): return Image.open(p).convert("RGBA")
def up(img): return img.resize((int(img.width*S), int(img.height*S)), Image.LANCZOS)

CHROME  = up(load(f"{AD}/chrome.png"))
CARDS   = [up(load(f"{AD}/card{i}.png")) for i in (1,2,3)]
DETAIL  = up(load(f"{AD}/detail_card.png"))

FONT_PILL = ImageFont.truetype(f"{FD}/Inter.ttf", int(46*S))
try: FONT_PILL.set_variation_by_axes([14, 550])
except Exception: pass

# geometry (virtual 1440p * S)
CHROME_POS  = (0, int(30*S))
CARD_POS    = [(int(221*S), int(344*S)), (int(948*S), int(344*S)), (int(1674*S), int(344*S))]
CARD_RECT1  = (int(221*S), int(344*S), int(884*S), int(1090*S))
DETAIL_POS  = (int(228*S), int(158*S))
DETAIL_RECT = (int(228*S), int(158*S), int(2331*S), int(1208*S))
ICON_START  = (int(1280*S), int(720*S), int(300*S))
ICON_LAND   = (int(255*S), int(135*S), int(70*S))
PILL_CY     = int(1250*S)
PILL_H      = int(96*S)
PILL_TEXT   = "AILA auto-selects best fit"

# timeline
T_HOLD   = 0.20
T_FLY    = (0.20, 0.85)
T_CHROME = (0.72, 1.05)
T_CARDS  = [(1.00, 1.48), (1.16, 1.64), (1.32, 1.80)]
T_PILL   = (2.30, 2.80)
T_PULSE  = (4.50, 5.20)
T_EXPAND = (5.20, 5.78)
T_SETTLE = (5.78, 6.40)

clamp = lambda x,a=0,b=1: max(a,min(b,x))
eoc = lambda t: 1-(1-clamp(t))**3
eic = lambda t: clamp(t)**3
eio = lambda t: (lambda u: u*u*(3-2*u))(clamp(t))
lerp = lambda a,b,t: a+(b-a)*t
def lerpc(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))

# ---------- rebuilt soft shadows (source shadows were cropped away) ----------
def make_shadow(w, h, radius, blur, alpha):
    sh = Image.new("RGBA", (w+blur*6, h+blur*6), (0,0,0,0))
    d = ImageDraw.Draw(sh)
    d.rounded_rectangle([blur*3, blur*3, blur*3+w, blur*3+h],
                        radius=radius, fill=(30,26,20,alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur))

CARD_BLUR   = int(18*S)
CARD_SHADOW = make_shadow(CARDS[0].width, CARDS[0].height, int(20*S), CARD_BLUR, 44)
DET_BLUR    = int(26*S)
DET_SHADOW  = make_shadow(DETAIL.width, DETAIL.height, int(28*S), DET_BLUR, 54)

def icon_img(sz):
    ic=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(ic)
    d.rounded_rectangle([0,0,sz,sz],radius=int(sz*0.21),fill=ICONBLU+(255,))
    f=ImageFont.truetype(f"{FD}/Inter.ttf",max(8,int(sz*0.565)))
    try: f.set_variation_by_axes([14,700])
    except Exception: pass
    bb=d.textbbox((0,0),"A.",font=f)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    d.text(((sz-tw)//2-bb[0],(sz-th)//2-bb[1]-int(sz*0.013)),"A.",font=f,fill=(255,255,255,255))
    return ic

def mini_ring(sz, t):
    """SPINNING comet ring mark for the pill (1 rotation/second)."""
    im=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(im)
    cx=cy=sz/2; R=sz*0.36
    head=(t*2*math.pi)%(2*math.pi)
    TRAIL=math.radians(300); STEPS=40
    for i in range(STEPS):
        f=i/(STEPS-1); ang=head-TRAIL*(1-f)
        x,y=cx+R*math.cos(ang),cy+R*math.sin(ang)
        col=lerpc(BLUE,ORANGE,f); a=int(255*(f**1.5))
        rr=R*0.10+(R*0.22-R*0.10)*f
        d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col+(a,))
    hx,hy=cx+R*math.cos(head),cy+R*math.sin(head)
    hr=R*0.24
    d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=ORANGE+(255,))
    return im

RING_SZ = int(64*S)

def build_pill_base():
    """pill without the ring (ring composited per-frame so it spins)"""
    pad=int(44*S)
    tmp=Image.new("RGB",(8,8)); tw=ImageDraw.Draw(tmp).textlength(PILL_TEXT,font=FONT_PILL)
    w=int(pad*2+RING_SZ+int(24*S)+tw)
    pill=Image.new("RGBA",(w+40,PILL_H+60),(0,0,0,0))
    sh=Image.new("RGBA",pill.size,(0,0,0,0))
    ImageDraw.Draw(sh).rounded_rectangle([20,20,20+w,20+PILL_H],radius=PILL_H//2,fill=(30,26,20,50))
    pill.alpha_composite(sh.filter(ImageFilter.GaussianBlur(int(10*S))),(0,int(6*S)))
    d=ImageDraw.Draw(pill)
    d.rounded_rectangle([20,20,20+w,20+PILL_H],radius=PILL_H//2,fill=(255,255,255,255))
    bb=d.textbbox((0,0),PILL_TEXT,font=FONT_PILL)
    d.text((20+pad+RING_SZ+int(24*S),20+(PILL_H-(bb[3]-bb[1]))//2-bb[1]),
           PILL_TEXT,font=FONT_PILL,fill=INK+(255,))
    return pill, 20+pad
PILL_BASE, PILL_RING_X = build_pill_base()

def alpha_mul(img, a):
    if a >= 1.0: return img
    out=img.copy()
    out.putalpha(out.getchannel("A").point(lambda v:int(v*a)))
    return out

def cover(src, w, h):
    s=max(w/src.width, h/src.height)
    sw,sh=max(2,int(src.width*s)),max(2,int(src.height*s))
    im=src.resize((sw,sh),Image.LANCZOS)
    return im.crop(((sw-w)//2,(sh-h)//2,(sw-w)//2+w,(sh-h)//2+h))

def rounded_mask_img(img, radius):
    m=Image.new("L",img.size,0)
    ImageDraw.Draw(m).rounded_rectangle([0,0,img.width-1,img.height-1],radius=radius,fill=255)
    out=img.copy(); out.putalpha(m)
    return out

def paste_card(img, k, x, y, a=1.0):
    if a<=0: return
    img.alpha_composite(alpha_mul(CARD_SHADOW,a),
        (x-CARD_BLUR*3, y-CARD_BLUR*3+int(14*S)))
    img.alpha_composite(alpha_mul(CARDS[k],a),(x,y))

def paste_detail(img, a=1.0):
    if a<=0: return
    img.alpha_composite(alpha_mul(DET_SHADOW,a),
        (DETAIL_POS[0]-DET_BLUR*3, DETAIL_POS[1]-DET_BLUR*3+int(18*S)))
    img.alpha_composite(alpha_mul(DETAIL,a),DETAIL_POS)

def draw_pill(img, t, a, dy=0):
    if a<=0: return
    x = W//2-PILL_BASE.width//2
    y = PILL_CY-PILL_BASE.height//2+dy
    img.alpha_composite(alpha_mul(PILL_BASE,a),(x,y))
    ring = mini_ring(RING_SZ, t)
    img.alpha_composite(alpha_mul(ring,a),
        (x+PILL_RING_X, y+20+(PILL_H-RING_SZ)//2))

def render_frame(i):
    t=i/FPS
    img=Image.new("RGBA",(W,H),BG+(255,))

    if t < T_EXPAND[0]:
        # ---- chrome ----
        if t>=T_CHROME[0]:
            ca=eoc((t-T_CHROME[0])/(T_CHROME[1]-T_CHROME[0]))
            dy=int((1-ca)*24*S)
            img.alpha_composite(alpha_mul(CHROME,ca),(CHROME_POS[0],CHROME_POS[1]+dy))

        # ---- cards cascade ----
        for k,(t0,t1) in enumerate(T_CARDS):
            p=eoc((t-t0)/(t1-t0)) if t>=t0 else 0.0
            if p<=0: continue
            dy=int((1-p)*90*S)
            paste_card(img,k,CARD_POS[k][0],CARD_POS[k][1]+dy,p)

        # ---- pill (spinning ring) ----
        if t>=T_PILL[0]:
            pp=eoc((t-T_PILL[0])/(T_PILL[1]-T_PILL[0]))
            draw_pill(img,t,pp,int((1-pp)*-36*S))

        # ---- selection pulse on card1 ----
        if t>=T_PULSE[0]:
            ph=(t-T_PULSE[0])/(T_PULSE[1]-T_PULSE[0])
            glow=0.5+0.5*math.sin(min(ph,1.0)*math.pi*2-math.pi/2)
            a=int(150*glow*eoc((t-T_PULSE[0])/0.3))
            if a>2:
                ov=Image.new("RGBA",(W,H),(0,0,0,0))
                d=ImageDraw.Draw(ov)
                x0,y0,x1,y1=CARD_RECT1
                for wd,aa in [(int(10*S),a),(int(20*S),a//3)]:
                    d.rounded_rectangle([x0-wd,y0-wd,x1+wd,y1+wd],
                        radius=int(30*S)+wd,outline=AZURE+(aa,),width=int(6*S))
                img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(int(3*S))))

        # ---- flying icon ----
        if t < T_FLY[1]+0.12:
            if t<T_FLY[0]: fx,fy,fs,fa=*ICON_START,1.0
            else:
                p=eio((t-T_FLY[0])/(T_FLY[1]-T_FLY[0]))
                fx=lerp(ICON_START[0],ICON_LAND[0],p)
                fy=lerp(ICON_START[1],ICON_LAND[1],p)
                fs=lerp(ICON_START[2],ICON_LAND[2],p)
                fa=1.0-eic((p-0.72)/0.28) if p>0.72 else 1.0
            ic=icon_img(max(8,int(fs)))
            img.alpha_composite(alpha_mul(ic,clamp(fa)),(int(fx-fs/2),int(fy-fs/2)))

    else:
        # ---- expansion: card1 rect -> detail rect, crossfade ----
        z=eoc((t-T_EXPAND[0])/(T_EXPAND[1]-T_EXPAND[0]))
        x0,y0,x1,y1=CARD_RECT1
        dx0,dy0,dx1,dy1=DETAIL_RECT
        rx0=int(lerp(x0,dx0,z)); ry0=int(lerp(y0,dy0,z))
        rx1=int(lerp(x1,dx1,z)); ry1=int(lerp(y1,dy1,z))
        rw,rh=max(2,rx1-rx0),max(2,ry1-ry0)

        if z<0.55:   # base scene fading out underneath
            ba=1-z/0.55
            img.alpha_composite(alpha_mul(CHROME,ba),CHROME_POS)
            for k in (1,2):
                paste_card(img,k,CARD_POS[k][0],CARD_POS[k][1],ba)
            draw_pill(img,t,ba)

        # growing shadow follows the morphing rect
        rad=int(lerp(20*S,28*S,z))
        blur=int(lerp(CARD_BLUR,DET_BLUR,z))
        sh=make_shadow(rw,rh,rad,blur,int(lerp(44,54,z)))
        img.alpha_composite(sh,(rx0-blur*3,ry0-blur*3+int(lerp(14,18,z)*S)))

        card_scaled=rounded_mask_img(cover(CARDS[0],rw,rh),rad)
        img.alpha_composite(card_scaled,(rx0,ry0))
        xa=eio((z-0.22)/0.6)
        if xa>0:
            det_scaled=rounded_mask_img(cover(DETAIL,rw,rh),rad)
            img.alpha_composite(alpha_mul(det_scaled,clamp(xa)),(rx0,ry0))

        # gentle settle after expansion
        if t>=T_SETTLE[0]:
            st=eio((t-T_SETTLE[0])/(T_SETTLE[1]-T_SETTLE[0]))
            sc=lerp(1.010,1.0,st)
            if sc>1.0004:
                w2,h2=int(W*sc),int(H*sc)
                full=img.resize((w2,h2),Image.LANCZOS)
                img=full.crop(((w2-W)//2,(h2-H)//2,(w2-W)//2+W,(h2-H)//2+H))

    return img.convert("RGB")

def main():
    out=sys.argv[1] if len(sys.argv)>1 else "aila_scene_05_4k.mp4"
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
