#!/usr/bin/env python3
"""Redraw Cha Cha, Miso, and matching Biscuit frames, plus a Peak + ICC court.

Original sticker art. Does not read or embed the personal reference photos.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ATH = os.path.join(ROOT, "Assets", "Resources", "Athletes")
COURT = os.path.join(ROOT, "Assets", "Resources", "Court")
FONT_CJK = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Canvas:
    def __init__(self, w, h, scale=2):
        self.w, self.h, self.s = w, h, scale
        self.im = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def ellipse(self, box, fill):
        s = self.s
        self.d.ellipse([v * s for v in box], fill=fill)

    def poly(self, pts, fill):
        s = self.s
        self.d.polygon([(x * s, y * s) for x, y in pts], fill=fill)

    def line(self, pts, fill, width):
        s = self.s
        self.d.line([(x * s, y * s) for x, y in pts], fill=fill, width=max(1, int(width * s)))

    def rot_ellipse(self, cx, cy, rx, ry, deg, fill, steps=36):
        ang = math.radians(deg)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for i in range(steps):
            t = 2 * math.pi * i / steps
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        self.poly(pts, fill)

    def disc(self, cx, cy, r, fill):
        self.ellipse([cx - r, cy - r, cx + r, cy + r], fill)

    def finish(self, sticker=6):
        alpha = self.im.split()[-1]
        k = sticker * 2 + 1
        if k % 2 == 0:
            k += 1
        dil = alpha.filter(ImageFilter.MaxFilter(k))
        white = Image.new("RGBA", self.im.size, (255, 255, 255, 255))
        white.putalpha(dil)
        out = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        out.alpha_composite(white)
        out.alpha_composite(self.im)
        out = out.resize((self.w, self.h), Image.Resampling.LANCZOS)
        box = out.getbbox()
        if not box:
            return out
        pad = 2
        return out.crop((
            max(0, box[0] - pad),
            max(0, box[1] - pad),
            min(out.width, box[2] + pad),
            min(out.height, box[3] + pad),
        ))


INK = (92, 46, 28, 255)
INK_DOG = (74, 36, 22, 255)


def cat_colors(kind):
    if kind == "chacha":
        return {
            "fur": (224, 136, 58, 255),
            "deep": (186, 96, 36, 255),
            "lite": (242, 186, 122, 255),
            "stripe": (168, 78, 30, 255),
            "white": (255, 248, 242, 255),
            "inner": (244, 190, 174, 255),
            "nose": (232, 142, 140, 255),
            "eye": (226, 156, 32, 255),
            "eye_hi": (255, 220, 120, 255),
            "pupil": (48, 28, 14, 255),
            "ink": INK,
        }
    return {
        "fur": (232, 150, 72, 255),
        "deep": (196, 112, 48, 255),
        "lite": (244, 190, 124, 255),
        "stripe": (176, 96, 40, 255),
        "white": (255, 253, 250, 255),
        "inner": (246, 198, 184, 255),
        "nose": (236, 154, 152, 255),
        "eye": (186, 204, 102, 255),
        "eye_hi": (232, 220, 140, 255),
        "pupil": (42, 52, 28, 255),
        "ink": INK,
    }


def draw_cat(kind, pose):
    p = cat_colors(kind)
    c = Canvas(480, 460, 2)
    fur, ink, white = p["fur"], p["ink"], p["white"]
    crouch = {"idle": 0, "ready": 18, "run": 8, "run2": 12, "jump": -8, "bump": 34, "spike": -6}[pose]
    leg = {"idle": 8, "ready": 14, "run": 26, "run2": -26, "jump": -8, "bump": 4, "spike": 18}[pose]

    def y(v):
        return v + crouch

    # Tail — a smooth curve of discs, behind the body.
    tail = {
        "idle": [(210, y(300)), (160, y(250)), (145, y(190)), (185, y(155))],
        "ready": [(215, y(320)), (165, y(300)), (150, y(250)), (175, y(210))],
        "run": [(200, y(310)), (150, y(300)), (130, y(250))],
        "run2": [(205, y(300)), (155, y(270)), (145, y(220))],
        "jump": [(248, y(300)), (190, y(310)), (160, y(270)), (185, y(230))],
        "bump": [(246, y(330)), (190, y(340)), (165, y(300)), (195, y(270))],
        "spike": [(248, y(300)), (190, y(310)), (155, y(270)), (180, y(230))],
    }[pose]
    for i in range(len(tail) - 1):
        ax, ay = tail[i]
        bx, by = tail[i + 1]
        steps = 6
        for s in range(steps):
            t = s / (steps - 1)
            cx, cy = ax + (bx - ax) * t, ay + (by - ay) * t
            rad = 17 - t * 5
            c.disc(cx, cy, rad + 4, ink)
            c.disc(cx, cy, rad, fur)
            if s % 2 == 1:
                c.disc(cx, cy, rad * 0.45, p["stripe"])

    # Haunch and hind leg.
    c.rot_ellipse(250, y(330), 46, 58, 8, ink)
    c.rot_ellipse(250, y(328), 36, 48, 8, fur)
    c.rot_ellipse(248, y(390), 18, 42, leg * 0.35, ink)
    c.rot_ellipse(248, y(390), 12, 34, leg * 0.35, p["deep"])
    c.disc(246 + leg * 0.15, y(428), 16, ink)
    c.disc(246 + leg * 0.15, y(428), 11, fur if kind == "chacha" else white)

    # Body.
    c.rot_ellipse(300, y(300), 78, 62, -8, ink)
    c.rot_ellipse(300, y(298), 66, 50, -8, fur)
    c.rot_ellipse(278, y(278), 40, 22, -12, p["deep"])
    c.rot_ellipse(318, y(318), 28, 22, -8, p["lite"])

    # Far foreleg.
    c.rot_ellipse(318, y(340), 16, 48, 18 + leg * 0.2, ink)
    c.rot_ellipse(318, y(340), 10, 38, 18 + leg * 0.2, p["deep"])

    # Near foreleg / arms by pose.
    if pose == "bump":
        c.rot_ellipse(360, y(300), 22, 36, -30, ink)
        c.rot_ellipse(360, y(300), 14, 26, -30, fur)
        c.disc(400, y(270), 20, ink)
        c.disc(400, y(270), 14, white if kind == "miso" else fur)
        c.disc(392, y(286), 16, ink)
        c.disc(392, y(286), 11, white if kind == "miso" else p["lite"])
    elif pose == "spike":
        c.rot_ellipse(370, y(250), 16, 58, -58, ink)
        c.rot_ellipse(370, y(250), 10, 48, -58, fur)
        c.disc(430, y(190), 18, ink)
        c.disc(430, y(190), 12, white if kind == "miso" else fur)
    elif pose == "jump":
        c.rot_ellipse(350, y(250), 16, 50, -40, ink)
        c.rot_ellipse(350, y(250), 10, 40, -40, fur)
        c.disc(390, y(200), 16, ink)
        c.disc(390, y(200), 11, white if kind == "miso" else fur)
    elif pose in ("run", "run2"):
        ang = -22 if pose == "run" else 26
        c.rot_ellipse(348, y(336), 16, 50, ang, ink)
        c.rot_ellipse(348, y(336), 10, 40, ang, fur)
        rad = math.radians(ang)
        paw_x = 348 - math.sin(rad) * 48
        paw_y = y(336) + math.cos(rad) * 48
        c.disc(paw_x, paw_y, 15, ink)
        c.disc(paw_x, paw_y, 10, white if kind == "miso" else fur)
    else:
        c.rot_ellipse(350, y(330), 16, 56, -6, ink)
        c.rot_ellipse(350, y(330), 10, 46, -6, fur)
        c.disc(358, y(392), 16, ink)
        c.disc(358, y(392), 11, white if kind == "miso" else fur)

    # Stripes on the back and thigh.
    c.rot_ellipse(275, y(280), 26, 7, 18, p["stripe"])
    c.rot_ellipse(268, y(305), 24, 6, 8, p["stripe"])
    c.rot_ellipse(262, y(330), 20, 6, -4, p["stripe"])
    if kind == "chacha":
        c.rot_ellipse(246, y(370), 12, 5, 70, p["stripe"])

    # Neck and head. Head stays in a similar place on grounded poses.
    hx, hy, hr = 345, y(188), 68
    if pose == "spike":
        hx, hy = 360, y(168)
    elif pose == "jump":
        hy = y(160)
    elif pose == "bump":
        hy = y(210)
        hx = 355
    c.ellipse([hx - 36, hy + 30, hx + 20, hy + 78], ink)
    c.ellipse([hx - 28, hy + 38, hx + 12, hy + 70], fur)
    c.disc(hx, hy, hr + 7, ink)
    c.disc(hx, hy, hr, fur)

    # Ears — far then near, rounded tips.
    def ear(pts, inner_k=0.42):
        c.poly(pts, ink)
        cx = sum(pt[0] for pt in pts) / 3
        cy = sum(pt[1] for pt in pts) / 3
        inset = [(cx + (x - cx) * 0.72, cy + (yy - cy) * 0.72) for x, yy in pts]
        c.poly(inset, fur)
        inner = [(cx + (x - cx) * inner_k, cy + (yy - cy) * inner_k) for x, yy in pts]
        c.poly(inner, p["inner"])

    ear([(hx - 48, hy - 8), (hx - 62, hy - 78), (hx - 10, hy - 28)])
    ear([(hx - 16, hy - 18), (hx + 8, hy - 92), (hx + 36, hy - 12)])

    # Forehead tabby bands.
    for i, dy in enumerate((-36, -18, -2)):
        c.rot_ellipse(hx - 4, hy + dy, 28 - i * 3, 6, -8, p["stripe"])

    if kind == "miso":
        c.ellipse([hx + 4, hy - 4, hx + hr + 6, hy + hr - 8], white)
        c.ellipse([hx - 8, hy + 18, hx + 48, hy + hr + 2], white)
        c.poly([(hx + 10, hy - 6), (hx + 28, hy + 16), (hx + 42, hy - 8), (hx + 22, hy - 22)], white)
    else:
        c.ellipse([hx + 18, hy + 10, hx + hr - 6, hy + 42], p["lite"])

    # Eye.
    ex, ey = hx + 10, hy - 6
    if pose == "bump":
        ey -= 4
    ew, eh = 22, 26
    if pose == "ready":
        eh = 20
    c.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], ink)
    c.ellipse([ex - ew + 4, ey - eh + 4, ex + ew - 4, ey + eh - 4], p["eye_hi"])
    c.ellipse([ex - ew + 6, ey - eh + 6, ex + ew - 6, ey + eh - 6], p["eye"])
    c.ellipse([ex - 4, ey - 10, ex + 10, ey + 12], p["pupil"])
    c.ellipse([ex - 1, ey - 8, ex + 6, ey - 1], (255, 255, 255, 255))

    # Nose and mouth.
    nx, ny = hx + 48, hy + 16
    c.poly([(nx, ny), (nx + 16, ny + 6), (nx + 6, ny + 16), (nx - 4, ny + 6)], p["nose"])
    c.line([(nx + 6, ny + 14), (nx + 6, ny + 24), (nx - 4, ny + 30)], ink, 3)
    c.line([(nx + 6, ny + 24), (nx + 16, ny + 28)], ink, 3)

    # Chest.
    if kind == "chacha":
        c.rot_ellipse(hx - 18, y(250), 14, 36, 8, white)
    else:
        c.ellipse([hx - 55, y(230), hx + 10, y(340)], white)
        c.ellipse([270, y(300), 360, y(370)], white)

    c.line([(nx + 8, ny + 8), (nx + 78, ny - 4)], ink, 2)
    c.line([(nx + 8, ny + 14), (nx + 80, ny + 16)], ink, 2)
    c.line([(nx + 8, ny + 20), (nx + 70, ny + 34)], ink, 2)
    return c.finish(6)


def draw_corgi(pose):
    c = Canvas(640, 420, 2)
    ink = INK_DOG
    red = (212, 114, 52, 255)
    red_d = (176, 82, 34, 255)
    white = (255, 252, 248, 255)
    inner = (242, 190, 176, 255)
    lift = {"idle": 0, "ready": 6, "run": 2, "run2": 6, "jump": -20, "bump": 0, "spike": -18}[pose]

    def y(v):
        return v + lift

    leg = {"idle": 0, "ready": 8, "run": 18, "run2": -18, "jump": -6, "bump": 0, "spike": 10}[pose]
    back_y = y(250 if pose in ("bump", "jump", "spike") else 268)
    tilt = {"bump": -16, "jump": -18, "spike": -14, "run": -8, "run2": -8}.get(pose, -4)
    c.rot_ellipse(250, back_y, 140, 64, tilt, ink)
    c.rot_ellipse(250, back_y - 2, 128, 52, tilt, red)
    c.rot_ellipse(220, back_y - 18, 70, 24, tilt, red_d)
    # White rump patch.
    c.rot_ellipse(150, back_y - 8, 42, 30, tilt, white)
    c.disc(118, back_y - 16, 14, ink)
    c.disc(118, back_y - 16, 9, white)

    # Hind legs, short.
    c.rot_ellipse(190, y(310), 22, 28, 8 + leg * 0.3, ink)
    c.rot_ellipse(190, y(310), 15, 20, 8 + leg * 0.3, red)
    c.disc(188 + leg * 0.2, y(345), 16, ink)
    c.disc(188 + leg * 0.2, y(345), 11, white)

    # Chest.
    c.rot_ellipse(390, y(285), 70, 48, 6, ink)
    c.rot_ellipse(390, y(283), 58, 38, 6, red)
    c.ellipse([350, y(270), 450, y(345)], white)

    # Front legs.
    if pose == "bump":
        c.rot_ellipse(470, y(330), 62, 16, 8, ink)
        c.rot_ellipse(470, y(328), 52, 10, 8, white)
        c.disc(530, y(338), 14, ink)
        c.disc(530, y(338), 10, white)
    elif pose in ("jump", "spike"):
        c.rot_ellipse(450, y(230), 16, 46, -36, ink)
        c.rot_ellipse(450, y(230), 10, 36, -36, white)
        c.disc(500, y(190), 14, ink)
        c.disc(500, y(190), 10, white)
    else:
        ang = 10 + leg
        c.rot_ellipse(430, y(320), 16, 36, ang * 0.4, ink)
        c.rot_ellipse(430, y(320), 10, 26, ang * 0.4, white)
        c.disc(445 + leg * 0.4, y(355), 14, ink)
        c.disc(445 + leg * 0.4, y(355), 10, white)

    if pose == "bump":
        hx, hy = 500, y(270)
    elif pose in ("jump", "spike"):
        hx, hy = 490, y(175)
    elif pose == "ready":
        hx, hy = 480, y(230)
    else:
        hx, hy = 470, y(235)
    c.rot_ellipse(hx, hy, 70, 56, -6, ink)
    c.rot_ellipse(hx, hy, 60, 46, -6, red)
    c.rot_ellipse(hx + 22, hy + 14, 40, 26, -6, white)
    c.poly([(hx + 6, hy + 6), (hx + 18, hy + 12), (hx + 10, hy - 40), (hx - 2, hy - 28)], white)

    def ear(tri):
        c.poly(tri, ink)
        cx = sum(pt[0] for pt in tri) / 3
        cy = sum(pt[1] for pt in tri) / 3
        c.poly([(cx + (x - cx) * 0.72, cy + (yy - cy) * 0.72) for x, yy in tri], red)
        c.poly([(cx + (x - cx) * 0.4, cy + (yy - cy) * 0.4) for x, yy in tri], inner)

    ear([(hx - 36, hy - 10), (hx - 8, hy - 100), (hx + 16, hy - 16)])
    ear([(hx - 6, hy - 22), (hx + 24, hy - 125), (hx + 70, hy - 8)])

    ex, ey = hx + 4, hy - 2
    c.ellipse([ex - 16, ey - 14, ex + 16, ey + 14], ink)
    c.ellipse([ex - 12, ey - 10, ex + 12, ey + 10], (92, 60, 36, 255))
    c.ellipse([ex - 5, ey - 6, ex + 7, ey + 8], (36, 24, 18, 255))
    c.ellipse([ex - 2, ey - 5, ex + 3, ey - 1], (255, 255, 255, 255))
    c.ellipse([hx + 46, hy + 4, hx + 68, hy + 22], (32, 26, 24, 255))
    if pose in ("idle", "ready", "run", "run2"):
        c.ellipse([hx + 30, hy + 28, hx + 52, hy + 48], (224, 96, 112, 255))
    return c.finish(6)


def draw_backdrop():
    W, H = 1920, 1080
    im = Image.new("RGBA", (W, H), (120, 176, 206, 255))
    d = ImageDraw.Draw(im)
    floor_y = int(round((1 - (0 - (-1.7)) / 10.8) * H))  # 910, matches the court

    for y in range(0, floor_y, 2):
        t = y / floor_y
        if t < 0.45:
            col = mix((186, 220, 236), (255, 214, 176), t / 0.45)
        else:
            col = mix((255, 214, 176), (255, 236, 214), (t - 0.45) / 0.55)
        d.line([(0, y), (W, y + 1)], fill=col + (255,), width=2)

    # Soft sun over the peak.
    d.ellipse([180, 70, 340, 220], fill=(255, 236, 196, 90))

    # Victoria Peak — green ridgeline on the west side of the view.
    d.polygon([(0, 700), (80, 560), (180, 430), (280, 300), (390, 250), (520, 310), (680, 480), (820, 640), (820, 760), (0, 760)], fill=(58, 122, 78, 255))
    d.polygon([(0, 700), (120, 620), (260, 500), (400, 430), (560, 520), (760, 680), (760, 760), (0, 760)], fill=(78, 146, 86, 255))
    d.polygon([(200, 520), (300, 400), (390, 360), (470, 430), (420, 560)], fill=(96, 158, 92, 255))
    # Peak Tower: a small original viewing deck on the summit, not a photo.
    d.rectangle([352, 300, 372, 360], fill=(236, 240, 242, 255))
    d.ellipse([328, 268, 396, 318], fill=(250, 252, 255, 255))
    d.ellipse([338, 278, 386, 308], fill=(120, 186, 206, 255))
    d.polygon([(390, 250), (470, 290), (430, 330), (360, 300)], fill=(186, 196, 168, 255))

    # Harbour between the peak and West Kowloon.
    for y in range(700, 830):
        t = (y - 700) / 130
        col = mix((64, 150, 176), (22, 78, 112), t)
        d.line([(0, y), (W, y)], fill=col + (255,))
    for y in range(720, 820, 16):
        d.arc([-30, y, W + 30, y + 16], 200, 340, fill=(210, 236, 240, 100), width=2)

    # A few lower Kowloon blocks, then ICC — the tall glass tower on the east side.
    sky = (36, 52, 68, 255)
    glass = (150, 186, 204, 255)
    d.rectangle([980, 560, 1060, 760], fill=sky)
    d.rectangle([1080, 500, 1160, 760], fill=sky)
    # ICC body. Taller than everything else, slightly narrower at the crown.
    d.polygon([(1240, 760), (1260, 210), (1380, 210), (1400, 760)], fill=(176, 204, 214, 255))
    d.polygon([(1260, 210), (1272, 150), (1368, 150), (1380, 210)], fill=(210, 226, 232, 255))
    d.rectangle([1288, 132, 1340, 154], fill=(90, 110, 124, 255))
    for wy in range(230, 740, 22):
        inset = int((wy - 210) * 0.04)
        for wx in range(1270 + inset, 1370 - inset, 16):
            if (wx + wy) % 48 == 0:
                continue
            d.rectangle([wx, wy, wx + 7, wy + 12], fill=(255, 236, 190, 220))
    d.rectangle([1180, 620, 1248, 760], fill=sky)
    d.rectangle([1410, 540, 1520, 760], fill=sky)
    d.rectangle([1540, 600, 1660, 760], fill=(48, 64, 78, 255))

    # Parapet and railing of the court, in front of the harbour.
    d.rectangle([0, 820, W, floor_y], fill=(214, 196, 170, 255))
    d.rectangle([0, 820, W, 834], fill=(160, 140, 116, 255))
    d.rectangle([0, 790, W, 800], fill=(70, 78, 84, 255))
    for x in range(16, W, 42):
        d.rectangle([x, 772, x + 5, 828], fill=(70, 78, 84, 255))

    try:
        cjk = ImageFont.truetype(FONT_CJK, 36)
        bold = ImageFont.truetype(FONT_BOLD, 22)
    except OSError:
        cjk = ImageFont.load_default()
        bold = cjk
    d.rounded_rectangle([70, 736, 280, 812], radius=10, fill=(24, 36, 32, 220))
    d.text((88, 742), "太平山", font=cjk, fill=(186, 230, 170, 255))
    d.text((92, 782), "THE PEAK", font=bold, fill=(230, 245, 220, 255))
    d.rounded_rectangle([1560, 700, 1840, 790], radius=10, fill=(20, 32, 44, 220))
    d.text((1620, 708), "ICC", font=bold, fill=(190, 230, 240, 255))
    d.text((1584, 744), "西九龍", font=cjk, fill=(255, 214, 160, 255))

    # String lights.
    for i, x in enumerate(range(30, 1900, 26)):
        col = ((255, 196, 120), (255, 150, 160), (150, 220, 210))[i % 3]
        d.ellipse([x, 804, x + 7, 811], fill=col + (255,))

    # Court deck. Floor line is the top of the slab.
    for y in range(floor_y, H):
        u = (y - floor_y) / max(1, H - floor_y)
        col = mix((232, 214, 186), (176, 150, 124), u)
        d.line([(0, y), (W, y)], fill=col + (255,))
    d.rectangle([0, floor_y, W, floor_y + 8], fill=(255, 250, 242, 255))

    def wx(x):
        return int(round((x - (-9.6)) / 19.2 * W))

    for xw in (-8.15, 8.15, 0):
        x = wx(xw)
        d.rectangle([x - 3, floor_y, x + 3, H - 10], fill=(255, 248, 240, 220))
    for xw in (-2.4, 2.4):
        x = wx(xw)
        d.rectangle([x - 2, floor_y + 10, x + 2, floor_y + 64], fill=(255, 248, 240, 170))
    cx = wx(0)
    d.rectangle([cx - 16, floor_y + 8, cx + 16, H], fill=(176, 64, 58, 255))
    d.rectangle([0, H - 16, W, H], fill=(42, 32, 28, 255))
    return im


def main():
    os.makedirs(ATH, exist_ok=True)
    os.makedirs(COURT, exist_ok=True)
    poses = ("idle", "ready", "bump", "spike", "run", "run2", "jump")
    for pose in poses:
        for kind in ("chacha", "miso"):
            path = os.path.join(ATH, f"{kind}_{pose}.png")
            draw_cat(kind, pose).save(path)
            print(path)
        path = os.path.join(ATH, f"biscuit_{pose}.png")
        draw_corgi(pose).save(path)
        print(path)
    bg = os.path.join(COURT, "backdrop.png")
    draw_backdrop().save(bg)
    print(bg)
    # Contact sheet for review.
    names = [f"{k}_{p}" for p in ("idle", "run", "run2", "jump", "bump", "spike") for k in ("chacha", "miso", "biscuit")]
    cell = 220
    cols = 6
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (36, 44, 52, 255))
    for i, name in enumerate(names):
        im = Image.open(os.path.join(ATH, name + ".png")).convert("RGBA")
        im.thumbnail((cell - 12, cell - 12))
        x = (i % cols) * cell + (cell - im.width) // 2
        y = (i // cols) * cell + (cell - im.height) // 2
        sheet.alpha_composite(im, (x, y))
    os.makedirs("/tmp/sprite-preview", exist_ok=True)
    sheet.convert("RGB").save("/tmp/sprite-preview/redraw.jpg", quality=90)
    court = Image.open(bg)
    court.thumbnail((960, 540))
    court.convert("RGB").save("/tmp/sprite-preview/peak-icc.jpg", quality=90)


if __name__ == "__main__":
    main()
