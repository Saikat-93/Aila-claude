#!/usr/bin/env python3
"""
Aila Launch Film — Scene 7: arrival chat over the cabin interior (4.2s).
Motion per sample (0619_3_.mp4): crossfade from scene 6, translucent user
bubble top-right, cream serif reply streams word-by-word below-left, hold.

Text:
  User:  We've arrived! Any hidden places or local experiences
         we shouldn't miss?
  AILA:  Absolutely. I've curated a personalized afternoon with
         scenic viewpoints, local cafés, a sunset trail, and the
         highest-rated dinner nearby.

Assets: bg/cabin.png (this scene), bg/paris.png + fonts (scene-6 handoff)
4K 3840x2160 @ 30fps.  Run:  python scene7.py aila_scene_07.mp4
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S      = 1.5
W, H   = int(2560*S), int(1440*S)
FPS    = 30
DUR    = 4.2
N      = int(DUR*FPS)

BUBBLE  = (238, 236, 228)
INK     = (20, 18, 14)
CREAM   = (252, 247, 240)
ORANGE  = (245, 166, 35)
BLUE    = (33, 150, 243)

GD = "./bg"
FD = "./fonts"

FONT_USER  = ImageFont.truetype(f"{FD}/Inter.ttf", int(78*S))
FONT_REPLY = ImageFont.truetype(f"{FD}/Lora.ttf",  int(75*S))
try:
    FONT_REPLY.set_variation_by_axes([500])
except Exception: pass

USER_TEXT  = "We've arrived! Any hidden places or local experiences we shouldn't miss?"
REPLY_TEXT = "Absolutely. I've curated a personalized afternoon with scenic viewpoints, local cafés, a sunset trail, and the highest-rated dinner nearby."

# geometry (1440p space)
BUB_RIGHT = W - int(160*S)
BUB_TOP     = int(170*S)
BUB_MAX_TW  = int(1250*S)
BUB_PAD_X   = int(70*S)
BUB_PAD_Y   = int(52*S)
BUB_LINE_H  = int(95*S)
BUB_RADIUS  = int(72*S)
BUB_ALPHA   = 170              # translucent like the sample

REPLY_X     = int(400*S)
REPLY_Y     = int(727*S)
REPLY_LH    = int(108*S)
REPLY_MAX_W = int(1720*S)

# timeline (s)
T_XFADE  = (0.00, 0.42)        # from scene-6 end state
T_RING   = 2.55                # ring appears as the reply lands
RING_CX, RING_CY = int(452*S), int(1128*S)
T_BUB    = (0.32, 0.70)
T_REPLY  = (0.95, 2.90)
KB       = (1.000, 1.040)

clamp = lambda x,a=0,b=1: max(a,min(b,x))
eoc = lambda t: 1-(1-clamp(t))**3
eio = lambda t: (lambda u: u*u*(3-2*u))(clamp(t))
lerp = lambda a,b,t: a+(b-a)*t
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

# ---------- cabin background master (bottom-left scrim for reply legibility) ----------
def build_bg():
    src = Image.open(f"{GD}/cabin.png").convert("RGB")
    s = max(W/src.width, H/src.height) * KB[1]
    mw, mh = int(src.width*s), int(src.height*s)
    m = src.resize((mw, mh), Image.LANCZOS)
    m = m.filter(ImageFilter.UnsharpMask(radius=2.0, percent=60, threshold=2))
    # radial-ish scrim: darker toward lower-left where the reply sits
    sc = Image.new("L", (128, 72))
    for yy in range(72):
        for xx in range(128):
            fx, fy = xx/128, yy/72
            v = 24 + 96*max(0.0, (1-fx*1.35))*max(0.0, (fy-0.28))
            sc.putpixel((xx,yy), int(clamp(v,0,120)))
    scrim = sc.resize((mw, mh), Image.BILINEAR)
    dark = Image.new("RGB", (mw, mh), (10, 10, 12))
    return Image.composite(dark, m, scrim)
MASTER = build_bg()
MW, MH = MASTER.size

def bg_frame(t):
    z = lerp(KB[0], KB[1], eio(t/DUR))
    cw, ch = int(W*KB[1]/z), int(H*KB[1]/z)
    cx, cy = MW//2, MH//2
    return MASTER.crop((cx-cw//2, cy-ch//2, cx-cw//2+cw, cy-ch//2+ch)).resize((W,H), Image.LANCZOS)

# ---------- scene-6 end state (for the crossfade in) ----------
def build_prev():
    lay = Image.open(f"{GD}/paris.png").convert("RGB")
    s = max(W/lay.width, H/lay.height)
    lay = lay.resize((int(lay.width*s), int(lay.height*s)), Image.LANCZOS)
    lay = lay.crop(((lay.width-W)//2,(lay.height-H)//2,
                    (lay.width-W)//2+W,(lay.height-H)//2+H))
    # scene-6 scrim + text + ring, matching scene6.py end state
    grad = Image.new("L", (W,1))
    for x in range(W):
        f=x/W; grad.putpixel((x,0), int(118*max(0.0,1.0-f*1.28)+30))
    scrim = grad.resize((W,H))
    lay = Image.composite(Image.new("RGB",(W,H),(8,9,12)), lay, scrim)
    lay = lay.convert("RGBA")
    F6 = ImageFont.truetype(f"{FD}/Lora.ttf", int(86*S))
    try: F6.set_variation_by_axes([500])
    except Exception: pass
    d = ImageDraw.Draw(lay)
    y = int(376*S)
    for i, ln in enumerate(["This journey is crafted just for you.", "",
                            "Every destination, stay, and experience",
                            "is personalized to match your",
                            "travel style, budget, and interests."]):
        if ln:
            d.text((int(317*S)+int(2*S), y+int(4*S)), ln, font=F6, fill=(0,0,0,96))
            d.text((int(317*S), y), ln, font=F6, fill=CREAM+(255,))
            y += int(122*S)
        else:
            y += int(41*S)
    draw_ring(lay, int(378*S), int(1030*S), 55*S, 0.0, 1.0)
    return lay.convert("RGB")

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

PREV = None  # built lazily in main to keep import light

# ---------- frosted user bubble (sample: translucent glass, cream text) ----------
BUB_LINES  = wrap_(USER_TEXT, FONT_USER, BUB_MAX_TW)
BUB_TW     = int(max(tlen(l, FONT_USER) for l in BUB_LINES))
BUB_W      = BUB_TW + 2*BUB_PAD_X
BUB_H      = len(BUB_LINES)*BUB_LINE_H + 2*BUB_PAD_Y - (BUB_LINE_H - int(78*S))
BUB_X      = BUB_RIGHT - BUB_W

def draw_frosted_bubble(img, alpha, dy):
    """glassmorphic bubble: blurred backdrop + light tint + faint border + cream text"""
    if alpha <= 0: return
    x0, y0 = BUB_X, BUB_TOP + dy
    region = img.crop((x0, y0, x0+BUB_W, y0+BUB_H)).convert("RGB")
    frost = region.filter(ImageFilter.GaussianBlur(int(36*S)))   # heavy waterglass blur
    # gentle lift that keeps the background's structure visible through the glass
    tint = Image.new("RGB", frost.size, (255, 255, 255))
    frost = Image.blend(frost, tint, 0.18)
    from PIL import ImageEnhance
    frost  = ImageEnhance.Brightness(frost).enhance(1.02)
    mask = Image.new("L", frost.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0,0,BUB_W-1,BUB_H-1], radius=BUB_RADIUS, fill=int(BUB_ALPHA*alpha))
    lay = Image.new("RGBA", frost.size, (0,0,0,0))
    lay.paste(frost, (0,0), mask)
    glass = Image.new(
    "RGBA",
    frost.size,
    (255, 255, 255, int(32 * alpha))
)
    lay.alpha_composite(glass)
    d = ImageDraw.Draw(lay)
    border = max(3, int(3*S))

    pad = border // 2 + 3

d.rounded_rectangle(
    [pad, pad, BUB_W-pad-1, BUB_H-pad-1],
    radius=BUB_RADIUS-pad,
    outline=(255,255,255,int(110*alpha)),
    width=border
)
ty = BUB_PAD_Y - int(8*S)
for i, ln in enumerate(BUB_LINES):
        d.text((BUB_PAD_X, ty+i*BUB_LINE_H), ln, font=FONT_USER,
               fill=(255,255,255,int(255*alpha)))          # left-aligned like the sample
img.alpha_composite(lay, (x0, y0))

# ---------- reply words ----------
def layout_reply():
    words=[]; space=tlen(" ",FONT_REPLY)
    x,y=REPLY_X,REPLY_Y
    for w in REPLY_TEXT.split(" "):
        wpx=tlen(w,FONT_REPLY)
        if x+wpx>REPLY_X+REPLY_MAX_W and x>REPLY_X:
            x=REPLY_X; y+=REPLY_LH
        words.append((w,x,y)); x+=wpx+space
    return words
R_WORDS = layout_reply()
N_R = len(R_WORDS)

def render_frame(i):
    global PREV
    t=i/FPS
    img=bg_frame(t).convert("RGBA")

    # crossfade from scene-6 end state
    if t < T_XFADE[1]+0.05:
        if PREV is None: PREV = build_prev()
        pa = 1.0-eio((t-T_XFADE[0])/(T_XFADE[1]-T_XFADE[0]))
        if pa>0:
            ov=PREV.convert("RGBA")
            ov.putalpha(Image.new("L",(W,H),int(255*pa)))
            img.alpha_composite(ov)

    # user bubble: frosted, fade + rise
    if t>=T_BUB[0]:
        p=eoc((t-T_BUB[0])/(T_BUB[1]-T_BUB[0]))
        draw_frosted_bubble(img, p, int((1-p)*46*S))

    # reply: streaming word-by-word, cream + soft shadow
    if t>=T_REPLY[0]-0.05:
        per=(T_REPLY[1]-T_REPLY[0])/N_R
        layer=Image.new("RGBA",(W,H),(0,0,0,0))
        ld=ImageDraw.Draw(layer)
        for j,(w,x,y) in enumerate(R_WORDS):
            a=eoc((t-(T_REPLY[0]+j*per))/0.15)
            if a<=0: break
            rise=int((1-a)*12*S)
            ld.text((x+int(2*S),y+rise+int(4*S)),w,font=FONT_REPLY,fill=(0,0,0,int(100*a)))
            ld.text((x,y+rise),w,font=FONT_REPLY,fill=CREAM+(int(255*a),))
        img.alpha_composite(layer)

    # comet ring below the reply (sample shows its mark here)
    if t >= T_RING:
        ra = eoc((t-T_RING)/0.30)
        draw_ring(img, RING_CX, RING_CY, 55*S, t, ra)

    return img.convert("RGB")

def main():
    out=sys.argv[1] if len(sys.argv)>1 else "aila_scene_07_4k.mp4"
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
