#!/usr/bin/env python3
"""
Aila Launch Film — Trail Discovery (full spot, 18s).
Recreates the sample (0619_4_.mp4) in the Aila visual language:

  1. 0.0–2.8   Company logo pops over the dark blurred cabin,
               comet ring draws itself around it.
  2. 2.6–7.9   Frosted user bubble (Inter, top-right) + Aila's cream
               Lora reply streaming word-by-word (below-left) + ring.
  3. 7.8–11.7  Three trail cards slide up, staggered (rebuilt native
               4K: Inter type, thumbnails from the source cards).
  4. 11.6–14.3 "Explore Nearby" map card scales in with a slow drift.
  5. 14.2–18.0 Mini card stack + closing lines streaming in Lora:
               "These recommendations are personalized for you. ..."
               + the spinning comet ring beneath (per the sample pic).

Assets: bg/cabin.png bg/logo.png bg/map.png bg/thumb-*.png
Fonts:  fonts/Inter.ttf fonts/Lora.ttf (variable)
4K 3840x2160 @ 30fps.
Run:    python trail_film.py trail_film_4k.mp4
Chunks: python trail_film.py chunk 0 90 part0.mp4   (for slow machines)
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S      = 1.5
W, H   = int(2560*S), int(1440*S)          # 3840 x 2160
FPS    = 30
DUR    = 18.0
N      = int(DUR*FPS)

CREAM   = (252, 247, 240)
INK     = (20, 18, 14)
ORANGE  = (245, 166, 35)
BLUE    = (33, 150, 243)
CHARCOAL= (58, 58, 60)                      # ring tail per the sample pic
GRAY    = (120, 124, 130)

GD = "./bg"
FD = "./fonts"

def _font(path, size, weight=None):
    f = ImageFont.truetype(path, int(size))
    if weight is not None:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f

FONT_USER   = _font(f"{FD}/Inter.ttf", 62*S, 480)     # user bubble
FONT_REPLY  = _font(f"{FD}/Lora.ttf",  70*S, 500)     # Aila reply
FONT_TITLE  = _font(f"{FD}/Inter.ttf", 62*S, 700)     # card title
FONT_SUB    = _font(f"{FD}/Inter.ttf", 44*S, 400)     # card subtitle
FONT_META   = _font(f"{FD}/Inter.ttf", 42*S, 550)     # card meta row
FONT_END_1  = _font(f"{FD}/Lora.ttf",  64*S, 600)     # closing line 1
FONT_END_B  = _font(f"{FD}/Lora.ttf",  52*S, 500)     # closing body

USER_TEXT  = "We're settling in at the cabin! Any short hikes nearby to keep our 5-year-old entertained?"
REPLY_TEXT = "Absolutely. There's plenty of wildlife around the trails here. I've found three easy, family-friendly hikes just minutes away."

END_LINES = [
    "These recommendations are personalized for you.",
    "Chosen using real traveler reviews,",
    "your current location, weather,",
    "and the time you have available today.",
]

CARDS = [   # thumb, title, subtitle, rating, difficulty, distance, duration
    ("thumb-pine.png",      "Pine Forest Trail", "Rocky Mountain National Park", "4.8", "Easy",     "1.4 mi", "0.5\u20131 hr"),
    ("thumb-waterfall.png", "Hidden Waterfall",  "Rocky Mountain National Park", "4.7", "Moderate", "1.5 mi", "1\u20132 hr"),
    ("thumb-beaver.png",    "Beaver Lake Loop",  "Rocky Mountain National Park", "4.6", "Easy",     "2.1 mi", "0.5\u20131 hr"),
]

# ---------------- timeline (seconds) ----------------
T_LOGO   = (0.00, 2.80)        # pop 0.05-0.75, ring draws, fade out last 0.4
T_BUB    = (2.60, 3.10)        # frosted bubble in
T_REPLY  = (3.60, 6.30)        # word streaming window
T_RING_C = 6.20                # chat ring lands as the reply finishes
T_CHATOUT= (7.40, 7.95)        # chat fades away
T_CARDS  = 7.80                # first card starts; stagger below
CARD_STAG= 0.35
T_CARDOUT= (11.20, 11.75)
T_MAP    = (11.60, 14.30)      # in 0.6s, drift, out last 0.45
T_END    = 14.20               # finale begins
T_ENDTXT = (15.00, 16.80)      # closing words stream
T_RING_E = 16.60               # ring pops under the text
KB       = (1.000, 1.055)      # Ken Burns push-in across the film

# geometry (1440p space, scaled by S)
LOGO_SIZE  = int(340*S)
LOGO_RING_R= 235*S
BUB_RIGHT  = W - int(150*S)
BUB_TOP    = int(150*S)
BUB_MAX_TW = int(1160*S)
BUB_PAD_X  = int(64*S)
BUB_PAD_Y  = int(48*S)
BUB_LINE_H = int(84*S)
BUB_RADIUS = int(64*S)
BUB_ALPHA  = 170
REPLY_X    = int(220*S)
REPLY_Y    = int(870*S)
REPLY_LH   = int(102*S)
REPLY_MAX_W= int(1500*S)
RING_C_XY  = (int(262*S), int(1236*S))
CARD_W, CARD_H = int(1450*S), int(400*S)
MINI_W, MINI_H = int(820*S),  int(226*S)
RING_E_R   = 52*S

clamp = lambda x,a=0,b=1: max(a,min(b,x))
eoc  = lambda t: 1-(1-clamp(t))**3
eio  = lambda t: (lambda u: u*u*(3-2*u))(clamp(t))
lerp = lambda a,b,t: a+(b-a)*t
def eob(t):                      # ease-out-back: slight overshoot for the logo pop
    t=clamp(t); c=1.70158*0.85
    return 1+ (c+1)*pow(t-1,3)+c*pow(t-1,2)
def lerpc(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))

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

# ---------------- background masters ----------------
def build_master(blur_px=0):
    src = Image.open(f"{GD}/cabin.png").convert("RGB")
    s = max(W/src.width, H/src.height) * KB[1]
    mw, mh = int(src.width*s), int(src.height*s)
    m = src.resize((mw, mh), Image.LANCZOS)
    if blur_px>0:
        m = m.filter(ImageFilter.GaussianBlur(blur_px))
    else:
        m = m.filter(ImageFilter.UnsharpMask(radius=2.0, percent=60, threshold=2))
    # directional scrim — darker lower-left where the reply text sits
    sc = Image.new("L", (128, 72))
    for yy in range(72):
        for xx in range(128):
            fx, fy = xx/128, yy/72
            v = 30 + 92*max(0.0,(1-fx*1.30))*max(0.0,(fy-0.25)) + 26*fy
            sc.putpixel((xx,yy), int(clamp(v,0,132)))
    scrim = sc.resize((mw, mh), Image.BILINEAR)
    dark = Image.new("RGB", (mw, mh), (10, 10, 12))
    return Image.composite(dark, m, scrim)

print("building backgrounds...", flush=True)
M_SHARP = build_master(0)
M_BLUR  = build_master(int(26*S))
MW, MH  = M_SHARP.size

def bg_frame(t):
    z = lerp(KB[0], KB[1], eio(t/DUR))
    cw, ch = int(W*KB[1]/z), int(H*KB[1]/z)
    cx, cy = MW//2, MH//2
    box = (cx-cw//2, cy-ch//2, cx-cw//2+cw, cy-ch//2+ch)
    # heavy blur during the logo scene, melts to sharp for the chat
    ba = 1.0 - eio((t - (T_LOGO[1]-0.55)) / 0.9)
    if ba >= 0.995:
        return M_BLUR.crop(box).resize((W,H), Image.LANCZOS)
    if ba <= 0.005:
        return M_SHARP.crop(box).resize((W,H), Image.LANCZOS)
    a = M_SHARP.crop(box).resize((W,H), Image.LANCZOS)
    b = M_BLUR.crop(box).resize((W,H), Image.LANCZOS)
    return Image.blend(a, b, ba)

# ---------------- comet ring (per the sample pic: charcoal tail -> gold head) ----------------
def draw_ring(img,cx,cy,R,t,alpha,trail_deg=300):
    if alpha<=0: return
    ov=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    head=(t*2*math.pi)%(2*math.pi); TRAIL=math.radians(trail_deg); STEPS=56
    for i in range(STEPS):
        f=i/(STEPS-1); ang=head-TRAIL*(1-f)
        x,y=cx+R*math.cos(ang),cy+R*math.sin(ang)
        col=lerpc(CHARCOAL,ORANGE,f**1.15)
        a=int(255*(0.28+0.72*(f**1.5))*alpha)
        rr=R*0.055+(R*0.16-R*0.055)*(f**1.4)
        d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col+(a,))
    hx,hy=cx+R*math.cos(head),cy+R*math.sin(head)
    hr=R*0.185
    glow=R*0.42
    d.ellipse([hx-glow,hy-glow,hx+glow,hy+glow],fill=ORANGE+(int(40*alpha),))
    d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=(253,210,110,int(255*alpha)))
    ov=ov.filter(ImageFilter.GaussianBlur(0.6*S))
    img.alpha_composite(ov)

# ---------------- scene 1: logo ----------------
LOGO_IMG = Image.open(f"{GD}/logo.png").convert("RGBA")
LOGO_IMG = LOGO_IMG.resize((LOGO_SIZE, int(LOGO_SIZE*LOGO_IMG.height/LOGO_IMG.width)), Image.LANCZOS)

def radial_glow(size, col, amax):
    g=Image.new("RGBA",(size,size),(0,0,0,0)); d=ImageDraw.Draw(g)
    for i in range(48,0,-1):
        f=i/48; r=size/2*f
        d.ellipse([size/2-r,size/2-r,size/2+r,size/2+r],
                  fill=col+(int(amax*(1-f)**1.6),))
    return g.filter(ImageFilter.GaussianBlur(size*0.04))
GLOW = radial_glow(int(900*S), ORANGE, 46)

def draw_logo_scene(img, t):
    a_in  = eoc((t-0.05)/0.45)
    a_out = 1.0 - eio((t-(T_LOGO[1]-0.42))/0.42)
    alpha = clamp(a_in)*clamp(a_out)
    if alpha<=0: return
    sc = 0.38 + 0.62*eob((t-0.05)/0.70)
    cx, cy = W//2, H//2
    pulse = 0.72 + 0.28*math.sin(t*3.2)
    gl = GLOW.resize((int(GLOW.width*sc),)*2, Image.BILINEAR)
    ga = gl.split()[3].point(lambda p:int(p*alpha*pulse)); gl.putalpha(ga)
    img.alpha_composite(gl,(cx-gl.width//2, cy-gl.height//2))
    ringR = LOGO_RING_R*sc
    prog  = eoc((t-0.18)/0.85)
    draw_ring(img, cx, cy, ringR, t*0.55, alpha, trail_deg=300*prog+18)
    lg = LOGO_IMG if abs(sc-1)<1e-3 else LOGO_IMG.resize(
        (max(1,int(LOGO_IMG.width*sc)), max(1,int(LOGO_IMG.height*sc))), Image.LANCZOS)
    if alpha<0.999:
        la=lg.split()[3].point(lambda p:int(p*alpha)); lg=lg.copy(); lg.putalpha(la)
    img.alpha_composite(lg,(cx-lg.width//2, cy-lg.height//2))

# ---------------- scene 2: frosted bubble + streaming reply ----------------
BUB_LINES = wrap_(USER_TEXT, FONT_USER, BUB_MAX_TW)
BUB_TW    = int(max(tlen(l, FONT_USER) for l in BUB_LINES))
BUB_W     = BUB_TW + 2*BUB_PAD_X
BUB_H     = len(BUB_LINES)*BUB_LINE_H + 2*BUB_PAD_Y - (BUB_LINE_H - int(66*S))
BUB_X     = BUB_RIGHT - BUB_W

def draw_frosted_bubble(img, alpha, dy):
    if alpha<=0: return
    x0, y0 = BUB_X, BUB_TOP + dy
    region = img.crop((x0, y0, x0+BUB_W, y0+BUB_H)).convert("RGB")
    frost = region.filter(ImageFilter.GaussianBlur(int(30*S)))
    frost = Image.blend(frost, Image.new("RGB",frost.size,(255,255,255)), 0.18)
    frost = ImageEnhance.Brightness(frost).enhance(1.02)
    mask = Image.new("L", frost.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0,0,BUB_W-1,BUB_H-1], radius=BUB_RADIUS, fill=int(BUB_ALPHA*alpha))
    lay = Image.new("RGBA", frost.size, (0,0,0,0))
    lay.paste(frost,(0,0),mask)
    glass = Image.new("RGBA", frost.size, (255,255,255,int(30*alpha)))
    gm = mask.point(lambda p: 255 if p>0 else 0)
    ga = glass.split()[3].point(lambda p:0); glass.putalpha(Image.composite(
        Image.new("L",frost.size,int(30*alpha)), ga, gm))
    lay = Image.alpha_composite(lay, glass)
    d = ImageDraw.Draw(lay)
    border=max(3,int(3*S)); pad=border//2+3
    d.rounded_rectangle([pad,pad,BUB_W-pad-1,BUB_H-pad-1],
        radius=BUB_RADIUS-pad, outline=(255,255,255,int(105*alpha)), width=border)
    ty = BUB_PAD_Y - int(6*S)
    for i,ln in enumerate(BUB_LINES):
        d.text((BUB_PAD_X, ty+i*BUB_LINE_H), ln, font=FONT_USER,
               fill=(255,255,255,int(255*alpha)))
    img.alpha_composite(lay,(x0,y0))

def layout_words(text, font, x0, y0, lh, mw):
    words=[]; space=tlen(" ",font); x,y=x0,y0
    for w in text.split(" "):
        wpx=tlen(w,font)
        if x+wpx>x0+mw and x>x0: x=x0; y+=lh
        words.append((w,x,y)); x+=wpx+space
    return words
R_WORDS = layout_words(REPLY_TEXT, FONT_REPLY, REPLY_X, REPLY_Y, REPLY_LH, REPLY_MAX_W)
N_R = len(R_WORDS)

def draw_chat_scene(img, t):
    a_out = 1.0 - eio((t-T_CHATOUT[0])/(T_CHATOUT[1]-T_CHATOUT[0]))
    if a_out<=0: return
    if t>=T_BUB[0]:
        p=eoc((t-T_BUB[0])/(T_BUB[1]-T_BUB[0]))
        draw_frosted_bubble(img, p*a_out, int((1-p)*44*S))
    if t>=T_REPLY[0]-0.05:
        per=(T_REPLY[1]-T_REPLY[0])/N_R
        layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
        for j,(w,x,y) in enumerate(R_WORDS):
            a=eoc((t-(T_REPLY[0]+j*per))/0.15)
            if a<=0: break
            rise=int((1-a)*12*S)
            ld.text((x+int(2*S),y+rise+int(4*S)),w,font=FONT_REPLY,fill=(0,0,0,int(100*a)))
            ld.text((x,y+rise),w,font=FONT_REPLY,fill=CREAM+(int(255*a),))
        if a_out<0.999:
            la=layer.split()[3].point(lambda p:int(p*a_out)); layer.putalpha(la)
        img.alpha_composite(layer)
    if t>=T_RING_C:
        ra=eoc((t-T_RING_C)/0.30)
        draw_ring(img, RING_C_XY[0], RING_C_XY[1], 46*S, t, ra*a_out)

# ---------------- trail cards, rebuilt native 4K ----------------
def draw_star(d,cx,cy,r,fill):
    pts=[]
    for i in range(10):
        ang=-math.pi/2+i*math.pi/5
        rr=r if i%2==0 else r*0.45
        pts.append((cx+rr*math.cos(ang),cy+rr*math.sin(ang)))
    d.polygon(pts,fill=fill)

def rounded_img(img,radius):
    m=Image.new("L",img.size,0)
    ImageDraw.Draw(m).rounded_rectangle([0,0,img.size[0]-1,img.size[1]-1],radius=radius,fill=255)
    out=img.convert("RGBA"); out.putalpha(m); return out

def with_shadow(card,blur,dy,alpha,pad):
    w,h=card.size
    cv=Image.new("RGBA",(w+pad*2,h+pad*2),(0,0,0,0))
    a=card.split()[3].point(lambda p:int(p*alpha/255))
    blk=Image.new("RGBA",card.size,(0,0,0,255)); blk.putalpha(a)
    sh=Image.new("RGBA",cv.size,(0,0,0,0)); sh.paste(blk,(pad,pad+dy),blk)
    sh=sh.filter(ImageFilter.GaussianBlur(blur))
    cv=Image.alpha_composite(cv,sh); cv.alpha_composite(card,(pad,pad))
    return cv

def build_card(thumb,title,sub,rating,diff,dist,dur,w,h,fs=1.0):
    ss=2; Wc,Hc=w*ss,h*ss
    ft=_font(f"{FD}/Inter.ttf",62*S*fs*ss,700)
    fu=_font(f"{FD}/Inter.ttf",44*S*fs*ss,400)
    fm=_font(f"{FD}/Inter.ttf",42*S*fs*ss,550)
    card=Image.new("RGBA",(Wc,Hc),(255,255,255,255)); d=ImageDraw.Draw(card)
    th=Image.open(f"{GD}/{thumb}").convert("RGB")
    tsz=Hc-int(90*S*fs*ss//1)
    tsz=Hc-int(46*S*fs)*ss*2
    th=th.resize((tsz,tsz),Image.LANCZOS)
    th=rounded_img(th,int(30*S*fs)*ss)
    m=int(46*S*fs)*ss
    card.alpha_composite(th,(m,m))
    tx=m+tsz+int(48*S*fs)*ss
    d.text((tx,int(58*S*fs)*ss),title,font=ft,fill=(17,24,39))
    d.text((tx,int(158*S*fs)*ss),sub,font=fu,fill=(120,124,130))
    my=int(266*S*fs)*ss
    sr=int(23*S*fs)*ss
    draw_star(d,tx+sr,my+int(24*S*fs)*ss,sr,(17,24,39))
    meta=f"{rating}    \u00b7    {diff}    \u00b7    {dist}    \u00b7    {dur}"
    d.text((tx+sr*2+int(18*S*fs)*ss,my),meta,font=fm,fill=(31,41,55))
    card=rounded_img(card,int(42*S*fs)*ss)
    return card.resize((w,h),Image.LANCZOS)

print("building cards...", flush=True)
CARDS_BIG=[with_shadow(build_card(*c,CARD_W,CARD_H),int(30*S),int(16*S),95,int(90*S)) for c in CARDS]
CARDS_MINI=[with_shadow(build_card(*c,MINI_W,MINI_H,fs=0.565),int(20*S),int(10*S),90,int(60*S)) for c in CARDS]

def paste_center(img,im,cx,cy,alpha=1.0):
    if alpha<=0.001: return
    if alpha<0.999:
        im=im.copy(); a=im.split()[3].point(lambda p:int(p*alpha)); im.putalpha(a)
    img.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

def draw_cards_scene(img,t):
    a_out=1.0-eio((t-T_CARDOUT[0])/(T_CARDOUT[1]-T_CARDOUT[0]))
    if a_out<=0: return
    gap=int(28*S)
    total=3*CARD_H+2*gap
    y=(H-total)//2; cx=W//2
    for i,card in enumerate(CARDS_BIG):
        tt=t-(T_CARDS+i*CARD_STAG)
        p=eoc(tt/0.60)
        if p<=0: break
        dy=int((1-p)*260*S)
        sc=0.955+0.045*p
        c=card if abs(sc-1)<1e-3 else card.resize(
            (int(card.width*sc),int(card.height*sc)),Image.BILINEAR)
        paste_center(img,c,cx,y+CARD_H//2+dy,p*a_out)
        y+=CARD_H+gap

# ---------------- map ----------------
mp=Image.open(f"{GD}/map.png")
import numpy as _np
_a=_np.array(mp); ys,xs=_np.where(_a[...,3]>10)
mp=mp.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
MAP_W=int(1640*S)
mp=mp.resize((MAP_W,int(mp.height*MAP_W/mp.width)),Image.LANCZOS)
MAP=with_shadow(mp,int(40*S),int(22*S),100,int(120*S))

def draw_map_scene(img,t):
    tt=t-T_MAP[0]
    if tt<0: return
    a_in=eoc(tt/0.55)
    a_out=1.0-eio((t-(T_MAP[1]-0.45))/0.45)
    alpha=a_in*clamp(a_out)
    if alpha<=0: return
    sc=(0.84+0.16*eoc(tt/0.65))*(1.0+0.05*eio(tt/(T_MAP[1]-T_MAP[0])))
    m=MAP.resize((int(MAP.width*sc),int(MAP.height*sc)),Image.BILINEAR)
    paste_center(img,m,W//2,H//2,alpha)

# ---------------- finale ----------------
EW=[]  # centered word layout for the closing lines
def build_end_words():
    out=[]; y=int(792*S)
    for i,line in enumerate(END_LINES):
        font=FONT_END_1 if i==0 else FONT_END_B
        lw=tlen(line,font); x=(W-lw)/2
        space=tlen(" ",font)
        for w in line.split(" "):
            out.append((w,x,y,font)); x+=tlen(w,font)+space
        y+=int((96 if i==0 else 74)*S)
    return out
EW=build_end_words()
N_E=len(EW)

def draw_end_scene(img,t):
    tt=t-T_END
    if tt<0: return
    # mini stack drops in
    p=eoc(tt/0.60)
    gap=int(18*S)
    y0=int(96*S)+int((1-p)*(-90*S))
    cx=W//2
    for i,c in enumerate(CARDS_MINI):
        pp=eoc((tt-i*0.10)/0.50)
        paste_center(img,c,cx,y0+MINI_H//2,pp)
        y0+=MINI_H+gap
    # closing lines stream word-by-word
    if t>=T_ENDTXT[0]-0.05:
        per=(T_ENDTXT[1]-T_ENDTXT[0])/N_E
        layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
        for j,(w,x,y,font) in enumerate(EW):
            a=eoc((t-(T_ENDTXT[0]+j*per))/0.15)
            if a<=0: break
            rise=int((1-a)*12*S)
            ld.text((x+int(2*S),y+rise+int(4*S)),w,font=font,fill=(0,0,0,int(110*a)))
            ld.text((x,y+rise),w,font=font,fill=CREAM+(int(255*a),))
        img.alpha_composite(layer)
    # comet ring — the sample-pic spinner, where the Claude logo sat
    if t>=T_RING_E:
        ra=eoc((t-T_RING_E)/0.30)
        draw_ring(img, W//2, int(1268*S), RING_E_R, t, ra)

# ---------------- frame assembly ----------------
def render_frame(i):
    t=i/FPS
    img=bg_frame(t).convert("RGBA")
    if t<T_LOGO[1]:            draw_logo_scene(img,t)
    if T_BUB[0]<=t<T_CHATOUT[1]: draw_chat_scene(img,t)
    if T_CARDS-0.1<=t<T_CARDOUT[1]: draw_cards_scene(img,t)
    if T_MAP[0]<=t<T_MAP[1]:   draw_map_scene(img,t)
    if t>=T_END:               draw_end_scene(img,t)
    return img.convert("RGB")

def main():
    if len(sys.argv)>2 and sys.argv[1]=="chunk":
        f0,f1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
        mov=[]
    else:
        f0,f1=0,N
        out=sys.argv[1] if len(sys.argv)>1 else "trail_film_4k.mp4"
        mov=["-movflags","+faststart"]
    cmd=["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p"]+mov+[out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    import time; t0=time.time()
    for i in range(f0,f1):
        p.stdin.write(render_frame(i).tobytes())
        if (i-f0)%15==0: print(f"frame {i} ({i-f0}/{f1-f0})  {time.time()-t0:.0f}s",flush=True)
    p.stdin.close(); p.wait()
    print("done:",out,f"({time.time()-t0:.0f}s)",flush=True)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="test":
        import os; os.makedirs("test_frames",exist_ok=True)
        for f in [15,45,75,100,140,175,210,265,310,355,400,440,470,505,530]:
            render_frame(f).resize((1280,720),Image.BILINEAR).save(
                f"test_frames/t{f:03d}.jpg",quality=90)
            print("test",f,flush=True)
    else:
        main()
