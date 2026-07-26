#!/usr/bin/env python3
"""
Aila spot — EXACT replica of sample 0619_4_.mp4 timing/motion/design.
All geometry measured from the sample at 720p and scaled x3 to 4K.
Sample timeline is preserved 1:1; a 0.45s logo pop-in is prefixed
(the sample clip starts with its logo already on screen) and the end
hold is kept at the sample's ~1.4s.

  SHIFT+0.00-0.70  panel rises from bottom over blurred cabin
                   (logo fades out underneath, exactly as sample)
  ......+0.35-0.75 reply streams fast while panel rises
  ......+0.72-1.10 conversation settles: chip locks to top
  ......+0.80-1.07 map card fades/scales in
  ......+1.07-1.50 trail card 1 slides up onto the map
  ......+0.85-1.90 "Aila" chip letters reveal
  ......+1.93-3.95 YOUR closing text streams in sentence bursts
  ......+3.60-4.65 carousel scrolls two cards (single eased glide)
  spark → spinning comet ring (per your sample pic), sits at content
  end and travels down as the text grows.

Assets: bg/cabin.png bg/logo.png bg/map.png bg/thumb-*.png
Fonts:  fonts/Inter.ttf fonts/Lora.ttf
4K 3840x2160 @ 30fps.  Run:  python replica.py out.mp4
Chunks: python replica.py chunk 0 90 part0.mp4
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

X3     = 3                       # sample 720p -> 4K
W, H   = 3840, 2160
FPS    = 30
SHIFT  = 0.45                    # logo pop-in prefix
DUR    = 5.55 + SHIFT            # sample 5.32s + logo prefix (+ tiny tail)
N      = int(DUR*FPS)

PANEL_BG   = (250, 248, 244)
BUBBLE_BG  = (240, 238, 231)
BUBBLE_TX  = (112, 108, 100)
INK        = (61, 57, 41)        # assistant serif ink
CHIP_TX    = (150, 146, 138)
ORANGE     = (217, 119, 87)      # sample spark orange
GOLD       = (253, 210, 110)
CHARCOAL   = (58, 58, 60)
CARD_TITLE = (17, 24, 39)
CARD_SUB   = (128, 132, 138)

GD, FD = "./bg", "./fonts"

def _font(p, s, wgt=None):
    f = ImageFont.truetype(p, int(s))
    if wgt:
        try: f.set_variation_by_axes([wgt])
        except Exception: pass
    return f

F_HDR   = _font(f"{FD}/Inter.ttf", 54, 650)   # "Aila v" header
F_USER  = _font(f"{FD}/Inter.ttf", 42, 450)   # user bubble
F_REPLY = _font(f"{FD}/Lora.ttf",  52, 500)   # assistant serif
F_CHIP  = _font(f"{FD}/Inter.ttf", 44, 480)
F_CT    = _font(f"{FD}/Inter.ttf", 52, 700)   # card title
F_CS    = _font(f"{FD}/Inter.ttf", 42, 400)   # card subtitle
F_CM    = _font(f"{FD}/Inter.ttf", 40, 550)   # card meta

USER_TEXT  = "We're already settling in! Any outdoor recommendations to keep this hyper 5-year-old distracted?"
REPLY_TEXT = "How about a short hike? There's lots of wildlife for Leo to see around the trails here. Let me find a few options nearby."
APP_NAME   = "Aila"

# YOUR closing text, streamed in sentence bursts like the sample
END_BURSTS = [
    "These recommendations are personalized for you.",
    "Chosen using real traveler reviews,",
    "your current location, weather,",
    "and the time you have available today.",
]
END_TEXT = " ".join(END_BURSTS)

CARDS = [
    ("thumb-beaver.png",    "Beaver Lake Loop",  "Rocky Mountain National Park", "4.6", "Easy",     "2.1 mi", "0.5\u20131 hr"),
    ("thumb-waterfall.png", "Hidden Waterfall",  "Rocky Mountain National Park", "4.7", "Moderate", "1.5 mi", "1\u20132 hr"),
    ("thumb-pine.png",      "Pine Forest Trail", "Rocky Mountain National Park", "4.8", "Easy",     "1.4 mi", "0.5\u20131 hr"),
]

# ---- measured geometry (720p x3) ----
PX, PW   = 365*X3, 549*X3            # panel x, width  (1095, 1647)
P_RAD    = 34*X3
HDR_H    = 190
BUB_RM   = 66                        # bubble right margin
BUB_PADX, BUB_PADY = 46, 40
BUB_RAD  = 48
BUB_LH   = 62
BUB_MAXW = 920
RE_X     = 105                       # reply/text left margin (35*3)
RE_LH    = 76
RE_MAXW  = PW - RE_X - 90
CHIP_X   = 120
MAP_X    = 40
MAP_W    = PW - 2*MAP_X              # 1567
CARD_W, CARD_H, CARD_GAP = 1180, 280, 20
MAP_H    = 1180
MAP_RADIUS = 24
RING_R   = 34

# ---- sample-measured timeline (seconds, sample-relative; +SHIFT applied) ----
T_RISE   = (0.20, 0.72)             # panel bottom -> top
T_SETTLE = (0.72, 1.10)             # second scroll: chip locks to top
T_LOGOF  = (0.10, 0.62)             # logo fade-out
T_REPLY  = (0.33, 0.75)             # fast word stream during rise
T_MAP    = (0.80, 1.07)             # map fade + scale
T_CARD1  = (1.07, 1.50)             # card 1 slides up
T_CHIP   = (0.85, 1.90)             # chip letters reveal
BURST_T  = [(1.93, 2.28), (2.62, 3.00), (3.18, 3.50), (3.62, 3.98)]
T_SCROLL = (3.60, 4.65)             # carousel glide, 2 steps
KB       = (1.000, 1.022)

clamp=lambda x,a=0,b=1: max(a,min(b,x))
eoc =lambda t: 1-(1-clamp(t))**3
eio =lambda t: (lambda u:u*u*(3-2*u))(clamp(t))
eob =lambda t:(lambda u,c=1.30158:1+(c+1)*pow(u-1,3)+c*pow(u-1,2))(clamp(t))
lerp=lambda a,b,t: a+(b-a)*t
def lerpc(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))

_t=Image.new("RGB",(8,8)); _M=ImageDraw.Draw(_t)
def tlen(s,f): return _M.textlength(s,font=f)
def wrap_(text,font,mw):
    out,cur=[],""
    for w in text.split(" "):
        t=(cur+" "+w).strip()
        if tlen(t,font)<=mw or not cur: cur=t
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out

# ---------------- background ----------------
print("background...", flush=True)
_src=Image.open(f"{GD}/cabin.png").convert("RGB")
_s=max(W/_src.width,H/_src.height)*KB[1]
MASTER=_src.resize((int(_src.width*_s),int(_src.height*_s)),Image.LANCZOS)
MASTER=MASTER.filter(ImageFilter.GaussianBlur(58))
# darken like the sample (right side darker) + slight global dim
_g=Image.new("L",(160,90))
for yy in range(90):
    for xx in range(160):
        fx=xx/160
        v=52+66*max(0.0,fx-0.35)+18*(yy/90)
        _g.putpixel((xx,yy),int(clamp(v,0,125)))
_scr=_g.resize(MASTER.size,Image.BILINEAR)
MASTER=Image.composite(Image.new("RGB",MASTER.size,(12,12,13)),MASTER,_scr)
MW,MH=MASTER.size

def bg_frame(t):
    z=lerp(KB[0],KB[1],eio(t/DUR))
    cw,ch=int(W*KB[1]/z),int(H*KB[1]/z)
    cx,cy=MW//2,MH//2
    return MASTER.crop((cx-cw//2,cy-ch//2,cx-cw//2+cw,cy-ch//2+ch)).resize((W,H),Image.BILINEAR)

# ---------------- comet ring (your spinner) ----------------
def draw_ring(d_img,cx,cy,R,t,alpha):
    if alpha<=0: return
    ov=Image.new("RGBA",d_img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    head=(t*2*math.pi)%(2*math.pi); TRAIL=math.radians(300); STEPS=40
    for i in range(STEPS):
        f=i/(STEPS-1); ang=head-TRAIL*(1-f)
        x,y=cx+R*math.cos(ang),cy+R*math.sin(ang)
        col=lerpc(CHARCOAL,(245,166,35),f**1.15)
        a=int(255*(0.30+0.70*f**1.5)*alpha)
        rr=R*0.06+(R*0.17-R*0.06)*(f**1.4)
        d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col+(a,))
    hx,hy=cx+R*math.cos(head),cy+R*math.sin(head)
    hr=R*0.19
    d.ellipse([hx-R*0.4,hy-R*0.4,hx+R*0.4,hy+R*0.4],fill=(245,166,35,int(38*alpha)))
    d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=GOLD+(int(255*alpha),))
    ov=ov.filter(ImageFilter.GaussianBlur(1.0))
    d_img.alpha_composite(ov)

# ---------------- logo ----------------
LOGO=Image.open(f"{GD}/logo.png").convert("RGBA")
LOGO=LOGO.resize((525,int(525*LOGO.height/LOGO.width)),Image.LANCZOS)
LOGO_CY=int(0.49*H)
T_FLY=(0.02,0.78)                # logo shrinks + flies to INTERCEPT the rising chip

def chip_screen(ts):
    return (PX+CHIP_X+33, sheet_screen_y(ts)+TOOL_TOP+33)

def draw_logo(img,t):
    ts=t-SHIFT
    a_in=eoc(t/0.30)
    if a_in<=0: return
    p=clamp((ts-T_FLY[0])/(T_FLY[1]-T_FLY[0]))
    if p>=1.0:
        # docked: ride the chip while crossfading out — seamless hand-off
        alpha=a_in*(1.0-clamp((ts-T_FLY[1])/0.12))
        if alpha<=0: return
        cx,cy=chip_screen(ts)
        lg=LOGO.resize((66,max(1,int(66*LOGO.height/LOGO.width))),Image.LANCZOS)
        a=lg.split()[3].point(lambda q:int(q*alpha)); lg.putalpha(a)
        img.alpha_composite(lg,(int(cx-lg.width/2),int(cy-lg.height/2)))
        return
    pe=p**2.15                   # ease-in acceleration (sample-measured)
    MX,MY=chip_screen(T_FLY[1]) # meeting point: where the chip will be at landing
    cx=lerp(W//2,MX,pe); cy=lerp(LOGO_CY,MY,pe)
    sc=(0.55+0.45*eob(t/0.38))*lerp(1.0,66/LOGO.width,p**1.9)
    lg=LOGO.resize((max(1,int(LOGO.width*sc)),max(1,int(LOGO.height*sc))),Image.LANCZOS)
    if a_in<0.999:
        a=lg.split()[3].point(lambda q:int(q*a_in)); lg.putalpha(a)
    img.alpha_composite(lg,(int(cx-lg.width/2),int(cy-lg.height/2)))

# ---------------- cards ----------------
def rounded_img(img,r):
    m=Image.new("L",img.size,0)
    ImageDraw.Draw(m).rounded_rectangle([0,0,img.size[0]-1,img.size[1]-1],radius=r,fill=255)
    o=img.convert("RGBA"); o.putalpha(m); return o

def build_card(thumb,title,sub,rating,diff,dist,dur):
    ss=2; Wc,Hc=CARD_W*ss,CARD_H*ss
    ft=_font(f"{FD}/Inter.ttf",46*ss,700)
    fu=_font(f"{FD}/Inter.ttf",38*ss,400)
    fm=_font(f"{FD}/Inter.ttf",35*ss,550)
    card=Image.new("RGBA",(Wc,Hc),(255,255,255,255)); d=ImageDraw.Draw(card)
    m=28*ss
    tsz=Hc-2*m
    th=Image.open(f"{GD}/{thumb}").convert("RGB").resize((tsz,tsz),Image.LANCZOS)
    card.alpha_composite(rounded_img(th,26*ss),(m,m))
    tx=m+tsz+40*ss
    d.text((tx,40*ss),title,font=ft,fill=CARD_TITLE)
    d.text((tx,116*ss),sub,font=fu,fill=CARD_SUB)
    my=196*ss; sr=19*ss
    pts=[]
    for i in range(10):
        ang=-math.pi/2+i*math.pi/5
        rr=sr if i%2==0 else sr*0.45
        pts.append((tx+sr+rr*math.cos(ang),my+22*ss+rr*math.sin(ang)))
    d.polygon(pts,fill=CARD_TITLE)
    d.text((tx+2*sr+16*ss,my),f"{rating}  \u00b7  {diff}  \u00b7  {dist}  \u00b7  {dur}",
           font=fm,fill=(45,52,62))
    card=rounded_img(card,28*ss)
    sh=Image.new("RGBA",(Wc+80,Hc+80),(0,0,0,0))
    blk=Image.new("RGBA",(Wc,Hc),(0,0,0,55))
    a=card.split()[3].point(lambda p:int(p*90/255)); blk.putalpha(a)
    s2=Image.new("RGBA",sh.size,(0,0,0,0)); s2.paste(blk,(40,50),blk)
    s2=s2.filter(ImageFilter.GaussianBlur(24))
    sh=Image.alpha_composite(sh,s2); sh.alpha_composite(card,(40,40))
    return sh.resize((sh.width//2,sh.height//2),Image.LANCZOS)   # back to 1x

print("cards...", flush=True)
CARD_IMGS=[build_card(*c) for c in CARDS]
CARD_PAD=20  # shadow pad at 1x

# ---------------- map ----------------
import numpy as _np
_mp=Image.open(f"{GD}/map.png").convert("RGBA")
_a=_np.array(_mp); ys,xs=_np.where(_a[...,3]>10)
_mp=_mp.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)).convert("RGB")
MAP_H = 1180
zoom = 1.00
scale = max(MAP_W / _mp.width, MAP_H / _mp.height) * zoom
new_w = int(_mp.width * scale)
new_h = int(_mp.height * scale)
tmp = _mp.resize((new_w, new_h), Image.LANCZOS)
left = (new_w - MAP_W) // 2 + 60
top = (new_h - MAP_H) // 2 + 10
_cont = tmp.crop((left, top, left + MAP_W, top + MAP_H))
_cont = _cont.filter(ImageFilter.UnsharpMask(radius=2.2, percent=72, threshold=2))
MAP_IMG = rounded_img(_cont, 24)

# chip icon = your logo, small
CHIP_ICON=Image.open(f"{GD}/logo.png").convert("RGBA").resize((66,66),Image.LANCZOS)

# ---------------- content sheet layout ----------------
BUB_LINES=wrap_(USER_TEXT,F_USER,BUB_MAXW)
BUB_TW=int(max(tlen(l,F_USER) for l in BUB_LINES))
BUB_W=BUB_TW+2*BUB_PADX
BUB_H=len(BUB_LINES)*BUB_LH+2*BUB_PADY-(BUB_LH-52)
BUB_Y=HDR_H+22

def layout_words(text,font,x0,y0,lh,mw):
    ws=[];sp=tlen(" ",font);x,y=x0,y0
    for w in text.split(" "):
        wp=tlen(w,font)
        if x+wp>x0+mw and x>x0: x=x0;y+=lh
        ws.append((w,x,y));x+=wp+sp
    return ws

REPLY_Y=BUB_Y+BUB_H+66
R_WORDS=layout_words(REPLY_TEXT,F_REPLY,RE_X,REPLY_Y,RE_LH,RE_MAXW)
REPLY_BOT=max(y for _,_,y in R_WORDS)+RE_LH

TOOL_TOP=REPLY_BOT+96            # chip y
MAP_Y=TOOL_TOP+66+60
TEXT_Y=MAP_Y+MAP_H+120
# continuous flow with burst index per word
E_WORDS=[]
_x,_y=RE_X,TEXT_Y
_sp=tlen(" ",F_REPLY)
for bi,burst in enumerate(END_BURSTS):
    for w in burst.split(" "):
        wp=tlen(w,F_REPLY)
        if _x+wp>RE_X+RE_MAXW and _x>RE_X: _x=RE_X; _y+=RE_LH
        E_WORDS.append((w,_x,_y,bi))
        _x+=wp+_sp
TEXT_BOT=_y+RE_LH
SHEET_H=max(TEXT_BOT+300, (TOOL_TOP-84)+H+140)   # panel always reaches screen bottom

# scroll targets (measured behaviour)
SCROLL1=BUB_Y-40                 # user bubble near top after rise
SCROLL2=TOOL_TOP-84              # chip locks to top (28px @720p, as sample)

def sheet_screen_y(ts):
    """screen y of sheet top. ts = sample-relative time."""
    r=eio((ts-T_RISE[0])/(T_RISE[1]-T_RISE[0]))
    y=lerp(H,-SCROLL1,r)
    s2=eio((ts-T_SETTLE[0])/(T_SETTLE[1]-T_SETTLE[0]))
    y-= (SCROLL2-SCROLL1)*s2
    return int(y)

def carousel_offset(ts):
    p=eio((ts-T_SCROLL[0])/(T_SCROLL[1]-T_SCROLL[0]))
    return p*2*(CARD_W+CARD_GAP)

def burst_alpha(ts,bi,wi_in_burst,n_burst):
    t0,t1=BURST_T[bi]
    per=(t1-t0)/max(1,n_burst)
    return eoc((ts-(t0+wi_in_burst*per))/0.12)

# precount words per burst
BURST_N=[len(b.split(" ")) for b in END_BURSTS]
def word_index_in_burst(i):
    bi=E_WORDS[i][3]; before=sum(BURST_N[:bi])
    return i-before

def render_sheet(ts):
    sh=Image.new("RGBA",(PW,SHEET_H),PANEL_BG+(255,))
    d=ImageDraw.Draw(sh)
    # header
    d.ellipse([70,HDR_H//2-42,70+84,HDR_H//2+42],fill=(240,238,231,255))
    for k in range(3):
        d.line([70+24,HDR_H//2-14+k*14,70+60,HDR_H//2-14+k*14],fill=(120,116,108,255),width=4)
    hdr=f"{APP_NAME} "
    hw=tlen(hdr,F_HDR)
    hx=(PW-hw-30)/2
    d.text((hx,HDR_H//2-30),hdr,font=F_HDR,fill=(70,66,56,255))
    cx=hx+hw+8; cy=HDR_H//2+6
    d.line([cx,cy-8,cx+13,cy+7],fill=(70,66,56,255),width=5)
    d.line([cx+13,cy+7,cx+26,cy-8],fill=(70,66,56,255),width=5)
    # user bubble
    bx=PW-BUB_RM-BUB_W
    d.rounded_rectangle([bx,BUB_Y,bx+BUB_W,BUB_Y+BUB_H],radius=BUB_RAD,fill=BUBBLE_BG+(255,))
    ty=BUB_Y+BUB_PADY-6
    for i,ln in enumerate(BUB_LINES):
        d.text((bx+BUB_PADX,ty+i*BUB_LH),ln,font=F_USER,fill=BUBBLE_TX+(255,))
    # reply words (fast stream during rise)
    per=(T_REPLY[1]-T_REPLY[0])/len(R_WORDS)
    for j,(w,x,y) in enumerate(R_WORDS):
        a=eoc((ts-(T_REPLY[0]+j*per))/0.10)
        if a<=0: break
        d.text((x,y),w,font=F_REPLY,fill=INK+(int(255*a),))
    reply_done=ts>=T_REPLY[1]
    # tool chip
    ca=eoc((ts-0.66)/0.12)
    if ca>0:
        ic=CHIP_ICON.copy()
        a=ic.split()[3].point(lambda p:int(p*ca)); ic.putalpha(a)
        sh.alpha_composite(ic,(CHIP_X,TOOL_TOP))
        n=len(APP_NAME)
        for li,ch in enumerate(APP_NAME):
            la=eoc((ts-(T_CHIP[0]+li*(T_CHIP[1]-T_CHIP[0])/n))/0.35)
            if la<=0: break
            xoff=CHIP_X+86+tlen(APP_NAME[:li],F_CHIP)
            d.text((xoff,TOOL_TOP+10),ch,font=F_CHIP,fill=CHIP_TX+(int(255*la),))
    # map
    ma=eoc((ts-T_MAP[0])/(T_MAP[1]-T_MAP[0]))
    if ma>0:
        msc=0.965+0.035*ma
        m=MAP_IMG if abs(msc-1)<1e-3 else MAP_IMG.resize(
            (int(MAP_W*msc),int(MAP_H*msc)),Image.BILINEAR)
        if ma<0.999:
            m=m.copy(); a=m.split()[3].point(lambda p:int(p*ma)); m.putalpha(a)
        sh.alpha_composite(m,(MAP_X+(MAP_W-m.width)//2,MAP_Y+(MAP_H-m.height)//2))
        # carousel (clipped to map width)
        strip=Image.new("RGBA",(MAP_W,CARD_H+CARD_PAD*2+40),(0,0,0,0))
        off=carousel_offset(ts)
        for ci,cimg in enumerate(CARD_IMGS):
            p=eoc((ts-(T_CARD1[0]+ci*0.10))/(T_CARD1[1]-T_CARD1[0]))
            if p<=0: continue
            dy=int((1-p)*70)
            x=30+ci*(CARD_W+CARD_GAP)-int(off)-CARD_PAD
            if x>MAP_W or x+cimg.width<0: continue
            c=cimg
            if p<0.999:
                c=c.copy(); a=c.split()[3].point(lambda q:int(q*p)); c.putalpha(a)
            strip.alpha_composite(c,(x,dy))
        sy=MAP_Y+MAP_H-CARD_H+35
        sh.alpha_composite(strip,(MAP_X,sy))
    # closing text bursts
    last_y=TEXT_Y
    any_word=False
    for i,(w,x,y,bi) in enumerate(E_WORDS):
        a=burst_alpha(ts,bi,word_index_in_burst(i),BURST_N[bi])
        if a<=0: break
        d.text((x,y),w,font=F_REPLY,fill=INK+(int(255*a),))
        last_y=y; any_word=True
    # comet ring at content end
    if reply_done or ts>0.5:
        if ts<T_MAP[0]:
            ry=REPLY_BOT+46
        elif not any_word:
            ry=TEXT_Y+30
        else:
            ry=last_y+RE_LH+52
        draw_ring(sh,RE_X+RING_R+6,ry,RING_R,ts*1.05,eoc((ts-0.45)/0.25))
    return sh

# panel side shadow (static)
SHADOW=Image.new("RGBA",(W,H),(0,0,0,0))
_sd=ImageDraw.Draw(SHADOW)
_sd.rectangle([PX-6,0,PX+PW+6,H],fill=(0,0,0,110))
SHADOW=SHADOW.filter(ImageFilter.GaussianBlur(40))

def render_frame(i):
    t=i/FPS
    ts=t-SHIFT
    img=bg_frame(t).convert("RGBA")
    if ts>=T_RISE[0]-0.02:
        ysh=sheet_screen_y(ts)
        if ysh<H:
            sa=eio((ts-T_RISE[0])/0.25)
            shd=SHADOW.copy()
            a=shd.split()[3].point(lambda p:int(p*sa)); shd.putalpha(a)
            top=max(0,ysh-30)
            img.alpha_composite(shd.crop((0,top,W,H)),(0,top))
            sheet=render_sheet(ts)
            # rounded top corners while rising
            if ysh>-P_RAD:
                m=Image.new("L",sheet.size,255)
                md=ImageDraw.Draw(m)
                md.rectangle([0,0,PW,P_RAD],fill=0)
                md.rounded_rectangle([0,0,PW-1,P_RAD*2+40],radius=P_RAD,fill=255)
                sheet.putalpha(m)
            crop_top=max(0,-ysh)
            vis=sheet.crop((0,crop_top,PW,min(SHEET_H,crop_top+H-max(0,ysh))))
            img.alpha_composite(vis,(PX,max(0,ysh)))
    draw_logo(img,t)
    return img.convert("RGB")

def main():
    if len(sys.argv)>2 and sys.argv[1]=="chunk":
        f0,f1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]; mov=[]
    else:
        f0,f1=0,N
        out=sys.argv[1] if len(sys.argv)>1 else "aila_spot_4k.mp4"
        mov=["-movflags","+faststart"]
    cmd=["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p"]+mov+[out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    import time;t0=time.time()
    for i in range(f0,f1):
        p.stdin.write(render_frame(i).tobytes())
        if (i-f0)%15==0: print(f"frame {i} ({i-f0}/{f1-f0}) {time.time()-t0:.0f}s",flush=True)
    p.stdin.close();p.wait()
    print("done:",out,flush=True)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="test":
        import os;os.makedirs("test_frames",exist_ok=True)
        for f in [6,14,20,26,32,40,48,58,72,90,110,125,140,155,170]:
            render_frame(f).resize((1280,720),Image.BILINEAR).save(
                f"test_frames/r{f:03d}.jpg",quality=90)
            print("test",f,flush=True)
    else: main()
