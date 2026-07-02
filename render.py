#!/usr/bin/env python3
"""
Aila Launch Film — Scenes 1–3, exact reference composition.

Composition (virtual 2560x1440, rendered at 1.5x = 4K):
  A) Text types INSIDE a growing #EEECE4 bubble, centered. Thin ink cursor.
  B) Send: whole bubble uniformly scales to 0.78x and docks top-right
     (right edge x=2176, top y=255). One clean scale+translate.
  C) Thinking: comet ring below-left (center ~x400), then reply types
     word-by-word in Lora at x=332 / y=770 while ring rides below the
     last line, easing downward when a new line wraps.

4K 3840x2160 @ 30fps, 8.0s.
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S      = 1.5
W, H   = int(2560*S), int(1440*S)
FPS    = 30
DUR    = 8.0
N      = int(DUR*FPS)

BG     = (250, 249, 244)   # #FAF9F4
BUBBLE = (238, 236, 228)   # #EEECE4
INK    = (20, 18, 14)      # #14120E
ORANGE = (245, 166, 35)    # #F5A623
BLUE   = (33, 150, 243)    # #2196F3

FD = "./fonts"
FONT_USER  = ImageFont.truetype(f"{FD}/Inter.ttf", int(100*S))
FONT_REPLY = ImageFont.truetype(f"{FD}/Lora.ttf",  int(76*S))
PLANE      = Image.open(f"{FD}/plane512.png").convert("RGBA")

USER_TEXT_1 = "Hi Aila,"
USER_TEXT_2 = "Hi Aila, I need a quick getaway this weekend."
REPLY_TEXT  = "Done. I've found the perfect itinerary, best stays, local experiences, and the lowest prices—all in one place."

# geometry (virtual px)
MAX_TEXT_W   = int(1460*S)     # text wrap width inside bubble
PAD_X        = int(92*S)
PAD_Y        = int(80*S)
LINE_H       = int(122*S)
CURSOR_W     = int(6*S)
CURSOR_H     = int(112*S)
CURSOR_GAP   = int(14*S)
CENTER       = (int(1280*S), int(728*S))     # typing bubble center
DOCK_RIGHT   = int(2176*S)                    # docked right edge
DOCK_TOP     = int(255*S)                     # docked top edge
DOCK_SCALE   = 0.78
RADIUS_MULTI = int(84*S)

REPLY_X      = int(332*S)
REPLY_Y      = int(770*S)
REPLY_LINE_H = int(110*S)
REPLY_MAX_W  = int(1750*S)
RING_CX      = int(396*S)
RING_R       = 56*S
RING_GAP     = int(150*S)     # gap from last reply baseline to ring center

# timeline (s)
T_BUBBLE_IN   = 0.30
T_TYPE1       = (0.55, 1.40)
T_TYPE2       = (2.10, 4.30)
T_SEND        = (5.00, 5.50)
T_THINK_IN    = 5.62
T_REPLY       = (6.60, 7.55)

clamp = lambda x,a=0,b=1: max(a, min(b, x))
eoc   = lambda t: 1-(1-clamp(t))**3            # ease-out cubic
eic   = lambda t: clamp(t)**3                  # ease-in cubic
eio   = lambda t: (lambda u: u*u*(3-2*u))(clamp(t))  # smoothstep

_tmp = Image.new("RGB",(8,8)); _MEAS = ImageDraw.Draw(_tmp)
def tlen(s, f): return _MEAS.textlength(s, font=f)

def wrap(text, font, max_w):
    out, cur = [], ""
    for w in text.split(" "):
        t = (cur+" "+w).strip()
        if tlen(t, font) <= max_w or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def typed(t, t0, t1, n):
    if t <= t0: return 0
    if t >= t1: return n
    return int(round(n*(t-t0)/(t1-t0)))

def rounded(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)

# ---------- bubble layer (typing state) ----------
def bubble_layer(shown, cursor_on, smooth_wh):
    """Render bubble+text+cursor onto transparent layer sized to bubble.
       smooth_wh: dict carrying smoothed w/h across frames."""
    lines = wrap(shown, FONT_USER, MAX_TEXT_W) if shown else [""]
    widths = [tlen(l, FONT_USER) for l in lines]
    text_w = max(widths) if shown else 0
    cur_extra = CURSOR_GAP + CURSOR_W
    tgt_w = int(text_w + cur_extra + 2*PAD_X)
    tgt_h = int(len(lines)*LINE_H + 2*PAD_Y - (LINE_H - int(100*S)))
    # smooth growth (ref bubble eases toward size)
    if smooth_wh["w"] is None:
        smooth_wh["w"], smooth_wh["h"] = tgt_w, tgt_h
    else:
        smooth_wh["w"] += (tgt_w - smooth_wh["w"]) * 0.42
        smooth_wh["h"] += (tgt_h - smooth_wh["h"]) * 0.42
    bw, bh = int(smooth_wh["w"]), int(smooth_wh["h"])

    layer = Image.new("RGBA", (bw+8, bh+8), (0,0,0,0))
    d = ImageDraw.Draw(layer)
    r = bh//2 if len(lines) == 1 else RADIUS_MULTI
    rounded(d, [4,4,4+bw,4+bh], r, BUBBLE+(255,))

    ty = 4 + (bh - (len(lines)*LINE_H - (LINE_H-int(100*S))))//2 - int(14*S)
    tx0 = 4 + PAD_X
    last_end = tx0
    for i, ln in enumerate(lines):
        d.text((tx0, ty + i*LINE_H), ln, font=FONT_USER, fill=INK+(255,))
        if i == len(lines)-1:
            last_end = tx0 + widths[i]
    if cursor_on:
        cy = ty + (len(lines)-1)*LINE_H + int(6*S)
        d.rectangle([last_end+CURSOR_GAP, cy, last_end+CURSOR_GAP+CURSOR_W, cy+CURSOR_H],
                    fill=INK+(255,))
    return layer

# ---------- final large bubble (for send morph + docked state) ----------
def final_bubble():
    return bubble_layer(USER_TEXT_2, False, {"w": None, "h": None})
FINAL = final_bubble()
FW, FH = FINAL.size
DOCKED = FINAL.resize((int(FW*DOCK_SCALE), int(FH*DOCK_SCALE)), Image.LANCZOS)

# ---------- comet ring ----------
def lerpc(c1, c2, t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))
def draw_ring(img, cx, cy, R, t, alpha):
    if alpha <= 0: return
    ov = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(ov)
    head = (t*2*math.pi) % (2*math.pi)          # 1 rot / sec
    TRAIL, STEPS = math.radians(300), 56
    for i in range(STEPS):
        f = i/(STEPS-1)
        ang = head - TRAIL*(1-f)
        x, y = cx+R*math.cos(ang), cy+R*math.sin(ang)
        col = lerpc(BLUE, ORANGE, f)            # blue tail -> orange head
        a = int(255*(f**1.6)*alpha)
        rr = R*0.055 + (R*0.16-R*0.055)*(f**1.4)
        d.ellipse([x-rr,y-rr,x+rr,y+rr], fill=col+(a,))
    hx, hy = cx+R*math.cos(head), cy+R*math.sin(head)
    hr = R*0.185
    d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr], fill=ORANGE+(int(255*alpha),))
    ov = ov.filter(ImageFilter.GaussianBlur(0.6*S))
    img.alpha_composite(ov)

# ---------- reply layout ----------
def layout_reply():
    ph = int(76*1.05*S)
    plane = PLANE.resize((ph, ph), Image.LANCZOS)
    space = tlen(" ", FONT_REPLY)
    items = [("img", plane)] + [("w", w) for w in REPLY_TEXT.split(" ")]
    placed, x, y = [], REPLY_X, REPLY_Y
    for kind, val in items:
        wpx = plane.width if kind == "img" else tlen(val, FONT_REPLY)
        if x + wpx > REPLY_X + REPLY_MAX_W and x > REPLY_X:
            x = REPLY_X; y += REPLY_LINE_H
        placed.append((kind, val, x, y, wpx))
        x += wpx + space
    return placed, plane
R_ITEMS, PLANE_SZ = layout_reply()
N_R = len(R_ITEMS)

SMOOTH = {"w": None, "h": None}
RING_Y_STATE = {"y": None}

def render_frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), BG+(255,))

    # ---------- A: typing bubble ----------
    if t < T_SEND[0]:
        if t >= T_BUBBLE_IN:
            if t < T_TYPE2[0]:
                shown = USER_TEXT_1[:typed(t, *T_TYPE1, len(USER_TEXT_1))]
            else:
                extra = USER_TEXT_2[len(USER_TEXT_1):]
                shown = USER_TEXT_1 + extra[:typed(t, *T_TYPE2, len(extra))]
            typing = T_TYPE1[0] <= t < T_TYPE1[1] or T_TYPE2[0] <= t < T_TYPE2[1]
            cur_on = typing or (t % 1.06) < 0.53
            lay = bubble_layer(shown, cur_on, SMOOTH)
            # pop-in
            a = eoc((t - T_BUBBLE_IN) / 0.28)
            sc = 0.92 + 0.08*a
            if sc < 1.0:
                lay = lay.resize((max(1,int(lay.width*sc)), max(1,int(lay.height*sc))), Image.LANCZOS)
            if a < 1.0:
                ach = lay.getchannel("A").point(lambda v: int(v*a))
                lay.putalpha(ach)
            img.alpha_composite(lay, (CENTER[0]-lay.width//2, CENTER[1]-lay.height//2))

    # ---------- B: send morph + docked ----------
    elif t < T_SEND[1]:
        p = eio((t - T_SEND[0]) / (T_SEND[1]-T_SEND[0]))
        sc = 1.0 + (DOCK_SCALE-1.0)*p
        w2, h2 = int(FW*sc), int(FH*sc)
        lay = FINAL.resize((w2, h2), Image.LANCZOS)
        # start center -> docked top-right
        sx, sy = CENTER[0]-FW//2, CENTER[1]-FH//2
        dx, dy = DOCK_RIGHT-int(FW*DOCK_SCALE), DOCK_TOP
        x = int(sx + (dx-sx)*p); y = int(sy + (dy-sy)*p)
        img.alpha_composite(lay, (x, y))
    else:
        img.alpha_composite(DOCKED, (DOCK_RIGHT-DOCKED.width, DOCK_TOP))

    # ---------- C: thinking ring + reply ----------
    if t >= T_THINK_IN - 0.05:
        # reply words
        n_on = 0
        if t >= T_REPLY[0]:
            per = (T_REPLY[1]-T_REPLY[0]) / N_R
            layer = Image.new("RGBA", (W, H), (0,0,0,0))
            ld = ImageDraw.Draw(layer)
            for j, (kind, val, x, y, wpx) in enumerate(R_ITEMS):
                a = eoc((t - (T_REPLY[0]+j*per)) / 0.14)
                if a <= 0: break
                n_on = j+1
                rise = int((1-a)*12*S)
                if kind == "img":
                    pl = PLANE_SZ.copy()
                    pl.putalpha(pl.getchannel("A").point(lambda v: int(v*a)))
                    layer.alpha_composite(pl, (int(x), int(y+rise+4*S)))
                else:
                    ld.text((x, y+rise), val, font=FONT_REPLY, fill=INK+(int(255*a),))
            img.alpha_composite(layer)

        # ring position: below last visible reply line (or default while thinking)
        if n_on > 0:
            last_y = R_ITEMS[n_on-1][3]
            tgt = last_y + RING_GAP + int(40*S)
        else:
            tgt = int(900*S)
        if RING_Y_STATE["y"] is None: RING_Y_STATE["y"] = tgt
        RING_Y_STATE["y"] += (tgt - RING_Y_STATE["y"]) * 0.22

        a = eoc((t - T_THINK_IN) / 0.30)
        sc = 0.85 + 0.15*eoc((t - T_THINK_IN) / 0.45)
        draw_ring(img, RING_CX, RING_Y_STATE["y"], RING_R*sc, t, clamp(a))

    return img.convert("RGB")

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/aila/aila_scene_01_03_4k.mp4"
    cmd = ["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
           "-r",str(FPS),"-i","-","-c:v","libx264","-preset","medium","-crf","16",
           "-pix_fmt","yuv420p","-movflags","+faststart",out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(N):
        p.stdin.write(render_frame(i).tobytes())
        if i % 30 == 0: print(f"frame {i}/{N}", flush=True)
    p.stdin.close(); p.wait()
    print("done:", out)

if __name__ == "__main__":
    main()
