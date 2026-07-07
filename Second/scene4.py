#!/usr/bin/env python3
"""
Aila Launch Film — Scene 4: "Aila Stay" connector card (ref 7s-10s, 3.0s).

Motion (measured from reference):
  0.00-0.90  previous scene (docked bubble + reply + ring) scrolls up & out
  0.95-1.30  card rises from below, decelerating to rest at center
  1.45-1.70  toggle flips ON (knob slides right, track -> azure)
  2.25-2.75  card collapses around the icon; icon grows ~229->300 and
             glides to exact screen center
  2.75-3.00  icon holds centered (handoff to next scene)

Branding: icon = "A." white on #0A6E9E rounded square, label "Aila Stay",
toggle azure #2493D6. 4K 3840x2160 @ 30fps.

Needs ./fonts/Inter.ttf, ./fonts/Lora.ttf, ./fonts/plane512.png
Run:  python scene4.py aila_scene_04.mp4
"""
import math, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S      = 1.5
W, H   = int(2560*S), int(1440*S)
FPS    = 30
DUR    = 3.0
N      = int(DUR*FPS)

BG      = (250, 249, 244)   # #FAF9F4
CARD    = (238, 236, 228)   # #EEECE4
INK     = (20, 18, 14)      # #14120E
ICONBLU = (10, 110, 158)    # #0A6E9E  (Aila icon blue)
AZURE   = (36, 147, 214)    # #2493D6  (toggle on)
TRACKOFF= (221, 218, 207)   # toggle off track
ORANGE  = (245, 166, 35)
BLUE    = (33, 150, 243)

FD = "./fonts"
FONT_USER  = ImageFont.truetype(f"{FD}/Inter.ttf", int(100*S))
FONT_REPLY = ImageFont.truetype(f"{FD}/Lora.ttf",  int(76*S))
FONT_LABEL = ImageFont.truetype(f"{FD}/Inter.ttf", int(78*S))
FONT_ICON  = ImageFont.truetype(f"{FD}/Inter.ttf", int(130*S))
try:  # bolder weights on the variable font where supported
    FONT_LABEL.set_variation_by_axes([14, 600])   # opsz, wght
    FONT_ICON.set_variation_by_axes([14, 700])
except Exception:
    pass
PLANE = Image.open(f"{FD}/plane512.png").convert("RGBA")

# ---- previous-scene text (must match render.py so the handoff is seamless)
USER_TEXT_2 = "Hi Aila, I need a quick getaway this weekend."
REPLY_TEXT  = "Done. I've found the perfect itinerary, best stays, local experiences, and the lowest prices—all in one place."
REPLY_TEXT  = re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]', '', REPLY_TEXT).strip()

LABEL_TEXT  = "Aila Stay"
ICON_TEXT   = "A."

# ---- geometry (virtual 2560x1440)
MAX_TEXT_W, PAD_X, PAD_Y = int(1460*S), int(92*S), int(80*S)
LINE_H       = int(122*S)
DOCK_RIGHT, DOCK_TOP, DOCK_SCALE = int(2176*S), int(255*S), 0.78
RADIUS_MULTI = int(84*S)
REPLY_X, REPLY_Y = int(332*S), int(770*S)
REPLY_LINE_H, REPLY_MAX_W = int(110*S), int(1750*S)
RING_CX, RING_R = int(396*S), 56*S

CARD_W, CARD_H = int(1731*S), int(470*S)
CARD_CX, CARD_CY = int(1280*S), int(762*S)
CARD_R   = int(96*S)
ICON_SZ  = int(229*S)
ICON_R   = int(48*S)
ICON_GAP = int(135*S)              # card left edge -> icon
LABEL_GAP= int(70*S)               # icon -> label
TGL_W, TGL_H = int(248*S), int(136*S)
TGL_MARGIN   = int(136*S)          # toggle right edge inset from card right
KNOB_INSET   = int(13*S)
END_ICON_SZ  = int(300*S)
END_CENTER   = (int(1280*S), int(720*S))

# ---- timeline (s)
T_SCROLL = (0.00, 0.90)
T_CARD   = (0.95, 1.30)
T_TOGGLE = (1.45, 1.70)
T_ZOOM   = (2.25, 2.75)

clamp = lambda x,a=0,b=1: max(a, min(b, x))
eoc = lambda t: 1-(1-clamp(t))**3
eic = lambda t: clamp(t)**3
eio = lambda t: (lambda u: u*u*(3-2*u))(clamp(t))
lerp = lambda a,b,t: a+(b-a)*t

_tmp=Image.new("RGB",(8,8)); _M=ImageDraw.Draw(_tmp)
def tlen(s,f): return _M.textlength(s,font=f)

def wrap_(text,font,mw):
    out,cur=[],""
    for w in text.split(" "):
        t=(cur+" "+w).strip()
        if tlen(t,font)<=mw or not cur: cur=t
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out

# ============ previous scene end-state (for scroll-out) ============
def build_prev_state():
    lay = Image.new("RGBA",(W,H),(0,0,0,0))
    d = ImageDraw.Draw(lay)
    # docked bubble
    lines = wrap_(USER_TEXT_2, FONT_USER, MAX_TEXT_W)
    widths=[tlen(l,FONT_USER) for l in lines]
    bw=int(max(widths)+int(20*S)+2*PAD_X); bh=int(len(lines)*LINE_H+2*PAD_Y-(LINE_H-int(100*S)))
    bub=Image.new("RGBA",(bw+8,bh+8),(0,0,0,0)); bd=ImageDraw.Draw(bub)
    bd.rounded_rectangle([4,4,4+bw,4+bh], radius=(bh//2 if len(lines)==1 else RADIUS_MULTI), fill=CARD+(255,))
    ty=4+(bh-(len(lines)*LINE_H-(LINE_H-int(100*S))))//2-int(14*S)
    for i,ln in enumerate(lines):
        bd.text((4+PAD_X,ty+i*LINE_H),ln,font=FONT_USER,fill=INK+(255,))
    dk=bub.resize((int(bub.width*DOCK_SCALE),int(bub.height*DOCK_SCALE)),Image.LANCZOS)
    lay.alpha_composite(dk,(DOCK_RIGHT-dk.width,DOCK_TOP))
    # reply
    ph=int(76*1.05*S); plane=PLANE.resize((ph,ph),Image.LANCZOS)
    space=tlen(" ",FONT_REPLY); x,y=REPLY_X,REPLY_Y; last_y=y
    lay.alpha_composite(plane,(int(x),int(y+4*S))); x+=plane.width+space
    for wd in REPLY_TEXT.split(" "):
        wpx=tlen(wd,FONT_REPLY)
        if x+wpx>REPLY_X+REPLY_MAX_W and x>REPLY_X: x=REPLY_X; y+=REPLY_LINE_H
        d.text((x,y),wd,font=FONT_REPLY,fill=INK+(255,)); x+=wpx+space; last_y=y
    return lay, last_y

PREV, PREV_LAST_Y = build_prev_state()
RING_Y = PREV_LAST_Y + int(190*S)

def lerpc(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))
def draw_ring(img,cx,cy,R,t,alpha):
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

# ============ card pieces ============
def icon_img(sz):
    ic=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(ic)
    d.rounded_rectangle([0,0,sz,sz],radius=int(ICON_R*sz/ICON_SZ),fill=ICONBLU+(255,))
    f=FONT_ICON
    if sz!=ICON_SZ:
        f=ImageFont.truetype(f"{FD}/Inter.ttf",int(130*S*sz/ICON_SZ))
        try: f.set_variation_by_axes([14,700])
        except Exception: pass
    bb=d.textbbox((0,0),ICON_TEXT,font=f)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    d.text(((sz-tw)//2-bb[0],(sz-th)//2-bb[1]-int(2*S)),ICON_TEXT,font=f,fill=(255,255,255,255))
    return ic

ICON_FULL=icon_img(ICON_SZ)

def soft_shadow(size_wh,radius,blur,alpha):
    sh=Image.new("RGBA",(size_wh[0]+blur*6,size_wh[1]+blur*6),(0,0,0,0))
    d=ImageDraw.Draw(sh)
    d.rounded_rectangle([blur*3,blur*3,blur*3+size_wh[0],blur*3+size_wh[1]],
                        radius=radius,fill=(30,26,20,alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur))

def draw_card(img, cx, cy, w, h, alpha, toggle_p, content_a):
    """card body+label+toggle (icon drawn separately). alpha 0..1, toggle_p 0..1"""
    if alpha<=0: return
    blur=int(26*S)
    sh=soft_shadow((w,h),int(CARD_R*w/CARD_W),blur,int(56*alpha))
    img.alpha_composite(sh,(int(cx-w/2-blur*3),int(cy-h/2-blur*3+int(18*S))))
    lay=Image.new("RGBA",(w+4,h+4),(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.rounded_rectangle([2,2,2+w,2+h],radius=int(CARD_R*w/CARD_W),fill=CARD+(int(255*alpha),))
    if content_a>0:
        ca=int(255*alpha*content_a)
        # label
        lx=ICON_GAP+ICON_SZ+LABEL_GAP - (CARD_W-w)//2
        bb=d.textbbox((0,0),LABEL_TEXT,font=FONT_LABEL)
        lh_=bb[3]-bb[1]
        d.text((lx,(h-lh_)//2-bb[1]),LABEL_TEXT,font=FONT_LABEL,fill=INK+(ca,))
        # toggle
        tx1=w-TGL_MARGIN+(0); tx0=tx1-TGL_W
        tx0=w-TGL_MARGIN-TGL_W; ty0=(h-TGL_H)//2
        track=lerpc(TRACKOFF,AZURE,eio(toggle_p))
        d.rounded_rectangle([tx0,ty0,tx0+TGL_W,ty0+TGL_H],radius=TGL_H//2,fill=track+(ca,))
        kd=TGL_H-2*KNOB_INSET
        kx=lerp(tx0+KNOB_INSET, tx0+TGL_W-KNOB_INSET-kd, eio(toggle_p))
        d.ellipse([kx,ty0+KNOB_INSET,kx+kd,ty0+KNOB_INSET+kd],fill=(255,255,255,ca))
    img.alpha_composite(lay,(int(cx-w/2),int(cy-h/2)))

def render_frame(i):
    t=i/FPS
    img=Image.new("RGBA",(W,H),BG+(255,))

    # ---- previous scene scrolling up & out ----
    if t < T_SCROLL[1]+0.05:
        p=eio((t-T_SCROLL[0])/(T_SCROLL[1]-T_SCROLL[0]))
        dy=int(-(H+80)*p)
        img.alpha_composite(PREV,(0,dy))
        draw_ring(img,RING_CX,RING_Y+dy,RING_R,t,1.0)

    # ---- card in / hold / zoom ----
    if t >= T_CARD[0]:
        if t < T_ZOOM[0]:
            p=eoc((t-T_CARD[0])/(T_CARD[1]-T_CARD[0]))
            cy=lerp(CARD_CY+int(620*S),CARD_CY,p)
            a=p
            tp=eio((t-T_TOGGLE[0])/(T_TOGGLE[1]-T_TOGGLE[0])) if t>=T_TOGGLE[0] else 0.0
            draw_card(img,CARD_CX,cy,CARD_W,CARD_H,a,tp,1.0)
            # icon at rest position on card
            ix=CARD_CX-CARD_W//2+ICON_GAP; iy=cy-ICON_SZ//2
            ic=ICON_FULL.copy()
            if a<1: ic.putalpha(ic.getchannel("A").point(lambda v:int(v*a)))
            img.alpha_composite(ic,(int(ix),int(iy)))
        else:
            z=eio((t-T_ZOOM[0])/(T_ZOOM[1]-T_ZOOM[0]))
            # card contracts around SCREEN CENTER (ref: center stays ~1280)
            w=int(lerp(CARD_W,END_ICON_SZ,z)); h=int(lerp(CARD_H,END_ICON_SZ,z))
            ccx=lerp(CARD_CX,END_CENTER[0],z); ccy=lerp(CARD_CY,END_CENTER[1],z)
            # icon glides from its rest position to screen center
            sz=int(lerp(ICON_SZ,END_ICON_SZ,z))
            ix0=CARD_CX-CARD_W//2+ICON_GAP+ICON_SZ//2
            cx=lerp(ix0,END_CENTER[0],z); cy=lerp(CARD_CY,END_CENTER[1],z)
            card_a=1.0-eic(z*1.15)
            draw_card(img,ccx,ccy,w,h,clamp(card_a),1.0,clamp(1.0-z*2.2))
            # soft shadow under icon grows at end
            if z>0.5:
                sa=int(46*(z-0.5)*2)
                sh=soft_shadow((sz,sz),int(ICON_R*sz/ICON_SZ),int(30*S),sa)
                img.alpha_composite(sh,(int(cx-sz/2-int(30*S)*3),int(cy-sz/2-int(30*S)*3+int(16*S))))
            ic=icon_img(sz)
            img.alpha_composite(ic,(int(cx-sz/2),int(cy-sz/2)))

    return img.convert("RGB")

def main():
    out=sys.argv[1] if len(sys.argv)>1 else "aila_scene_04_4k.mp4"
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
