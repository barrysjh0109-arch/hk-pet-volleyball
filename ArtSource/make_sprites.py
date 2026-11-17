#!/usr/bin/env python3
"""Original sticker sprites for HK Pet Volleyball.

Hand-authored arcade art. Does not read, crop, or embed the personal
reference photos. Markings follow the Phase 0 model notes:
  Cha Cha  — compact ginger tabby, amber eyes, small white chest blaze
  Miso     — orange tabby cap and back, white muzzle / chest / paws, green-gold eyes
  Biscuit  — long low Pembroke, red-and-white, forehead blaze, big ears, white rump
             (no harness, no clothing)
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ATH = os.path.join(ROOT, "Assets", "Resources", "Athletes")
COURT = os.path.join(ROOT, "Assets", "Resources", "Court")
PREVIEW = "/tmp/sprite-preview"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_CJK = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


class Canvas:
    def __init__(self, w, h, scale=2):
        self.w = w
        self.h = h
        self.s = scale
        self.im = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def _b(self, box):
        s = self.s
        return [box[0] * s, box[1] * s, box[2] * s, box[3] * s]

    def ellipse(self, box, fill):
        self.d.ellipse(self._b(box), fill=fill)

    def poly(self, pts, fill):
        s = self.s
        self.d.polygon([(x * s, y * s) for x, y in pts], fill=fill)

    def line(self, pts, fill, width):
        s = self.s
        self.d.line([(x * s, y * s) for x, y in pts], fill=fill, width=max(1, int(width * s)))

    def rot_ellipse(self, cx, cy, rx, ry, deg, fill, steps=40):
        ang = math.radians(deg)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for i in range(steps):
            t = 2 * math.pi * i / steps
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        self.poly(pts, fill)

    def stroke_ellipse(self, box, fill, outline, width):
        self.ellipse(box, outline)
        self.ellipse(
            [box[0] + width, box[1] + width, box[2] - width, box[3] - width],
            fill,
        )

    def finish(self, sticker=8):
        # White die-cut edge from the alpha, then downscale.
        alpha = self.im.split()[-1]
        dil = alpha.filter(ImageFilter.MaxFilter(sticker * 2 + 1))
        white = Image.new("RGBA", self.im.size, (255, 255, 255, 255))
        white.putalpha(dil)
        out = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        out.alpha_composite(white)
        out.alpha_composite(self.im)
        out = out.resize((self.w, self.h), Image.Resampling.LANCZOS)
        # Crop to opaque bounds with a small pad so pivots stay predictable,
        # but keep the bottom row if feet sit on it — pad evenly except we
        # want feet near the bottom. Tight crop is fine; the game fits sprites
        # by their bounds and pins the bottom to the floor.
        bbox = out.getbbox()
        if bbox:
            pad = 2
            l = max(0, bbox[0] - pad)
            t = max(0, bbox[1] - pad)
            r = min(out.width, bbox[2] + pad)
            b = min(out.height, bbox[3] + pad)
            out = out.crop((l, t, r, b))
        return out


INK = (92, 48, 28, 255)
INK_DOG = (74, 36, 22, 255)


def cat_palette(kind):
    if kind == "chacha":
        return {
            "fur": (224, 132, 58, 255),
            "fur_lite": (240, 176, 112, 255),
            "fur_deep": (196, 104, 40, 255),
            "stripe": (166, 78, 28, 255),
            "stripe_d": (140, 62, 24, 255),
            "white": (255, 246, 238, 255),
            "inner": (242, 186, 168, 255),
            "nose": (232, 140, 138, 255),
            "eye": (227, 155, 30, 255),
            "eye_hi": (255, 214, 110, 255),
            "pupil": (48, 28, 16, 255),
            "ink": INK,
        }
    return {
        "fur": (233, 150, 74, 255),
        "fur_lite": (244, 186, 120, 255),
        "fur_deep": (208, 122, 52, 255),
        "stripe": (184, 96, 36, 255),
        "stripe_d": (156, 78, 30, 255),
        "white": (255, 252, 250, 255),
        "inner": (246, 198, 184, 255),
        "nose": (236, 150, 150, 255),
        "eye": (176, 196, 96, 255),
        "eye_hi": (226, 214, 120, 255),
        "pupil": (42, 48, 28, 255),
        "ink": INK,
    }


def draw_cat(pose, kind):
    p = cat_palette(kind)
    c = Canvas(560, 520, 2)
    ink = p["ink"]
    fur = p["fur"]
    # Pose offsets. y grows downward. Ground line sits near y=500.
    crouch = {"idle": 0, "ready": 36, "bump": 78, "spike": -18}[pose]
    lean = {"idle": -8, "ready": 10, "bump": -4, "spike": 18}[pose]

    def y(v):
        return v + crouch

    # Tail, behind the body.
    tail_pts = {
        "idle": [(250, y(390)), (180, y(340)), (150, y(250)), (190, y(180)), (250, y(200))],
        "ready": [(255, y(400)), (190, y(390)), (160, y(330)), (180, y(280))],
        "bump": [(270, y(430)), (200, y(400)), (170, y(340)), (210, y(300))],
        "spike": [(230, y(360)), (150, y(390)), (120, y(330)), (160, y(280))],
    }[pose]
    c.line(tail_pts, ink, 36)
    c.line(tail_pts, fur, 24)
    # Tail stripes.
    for i in range(0, len(tail_pts) - 1):
        ax, ay_ = tail_pts[i]
        bx, by = tail_pts[i + 1]
        mx, my = (ax + bx) / 2, (ay_ + by) / 2
        c.ellipse([mx - 10, my - 8, mx + 10, my + 8], p["stripe"])

    # Hind leg / haunch.
    if pose == "spike":
        c.rot_ellipse(300, y(400), 36, 70, 28, ink)
        c.rot_ellipse(300, y(400), 28, 60, 28, fur)
        c.ellipse([318, y(448), 368, y(492)], ink)
        c.ellipse([326, y(456), 360, y(486)], fur)
    elif pose == "bump":
        c.rot_ellipse(292, y(430), 40, 48, 10, ink)
        c.rot_ellipse(292, y(430), 32, 38, 10, fur)
        c.ellipse([300, y(455), 360, y(500)], ink)
        c.ellipse([308, y(462), 352, y(494)], p["fur_deep"])
    else:
        c.rot_ellipse(288, y(400), 40, 78, 8, ink)
        c.rot_ellipse(288, y(400), 31, 68, 8, fur)
        c.ellipse([276, y(455), 338, y(508)], ink)
        c.ellipse([284, y(464), 330, y(500)], fur)

    # Body.
    c.rot_ellipse(330, y(330), 108, 78, lean, ink)
    c.rot_ellipse(330, y(328), 96, 66, lean, fur)
    # Back shade.
    c.rot_ellipse(300, y(300), 70, 36, lean - 10, p["fur_deep"])
    # Belly highlight.
    c.rot_ellipse(355, y(355), 48, 32, lean, p["fur_lite"])

    # Chest / second foreleg (far).
    if pose == "spike":
        c.rot_ellipse(360, y(300), 28, 70, 50, ink)
        c.rot_ellipse(360, y(300), 20, 60, 50, fur)
    else:
        c.rot_ellipse(345, y(360), 26, 64, 16, ink)
        c.rot_ellipse(345, y(360), 18, 54, 16, p["fur_deep"])

    # Near foreleg / bump arms / spike arm.
    if pose == "bump":
        # Both paws stacked up in front of the chest.
        c.rot_ellipse(400, y(360), 30, 46, -20, ink)
        c.rot_ellipse(400, y(360), 22, 36, -20, fur)
        c.ellipse([390, y(300), 470, y(360)], ink)
        c.ellipse([400, y(310), 460, y(350)], fur)
        c.ellipse([418, y(318), 456, y(348)], p["fur_lite"])
    elif pose == "spike":
        c.rot_ellipse(430, y(250), 26, 78, -55, ink)
        c.rot_ellipse(430, y(250), 18, 68, -55, fur)
        # Hitting paw.
        c.rot_ellipse(500, y(175), 28, 22, -20, ink)
        c.rot_ellipse(500, y(175), 20, 15, -20, fur)
    elif pose == "ready":
        c.rot_ellipse(400, y(355), 28, 72, -28, ink)
        c.rot_ellipse(400, y(355), 20, 62, -28, fur)
        c.ellipse([430, y(400), 486, y(448)], ink)
        c.ellipse([438, y(408), 478, y(440)], fur)
    else:
        c.rot_ellipse(385, y(350), 28, 74, -8, ink)
        c.rot_ellipse(385, y(350), 20, 64, -8, fur)
        c.ellipse([392, y(410), 448, y(468)], ink)
        c.ellipse([400, y(418), 440, y(460)], fur)

    # Neck and head.
    c.ellipse([335, y(210), 410, y(280)], ink)
    c.ellipse([345, y(218), 400, y(272)], fur)
    hx, hy, hr = 400, y(175), 86
    c.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], ink)
    c.ellipse([hx - hr + 10, hy - hr + 10, hx + hr - 10, hy + hr - 10], fur)

    # Ears. Far ear first.
    if pose == "spike":
        far = [(350, y(130)), (300, y(40)), (400, y(95))]
        near = [(400, y(115)), (455, y(8)), (490, y(120))]
    elif pose == "bump":
        far = [(345, y(150)), (310, y(70)), (395, y(120))]
        near = [(405, y(140)), (470, y(28)), (500, y(145))]
    elif pose == "ready":
        far = [(348, y(140)), (315, y(48)), (400, y(108))]
        near = [(400, y(125)), (470, y(12)), (505, y(130))]
    else:
        far = [(345, y(135)), (300, y(40)), (395, y(105))]
        near = [(395, y(120)), (455, y(4)), (500, y(125))]
    c.poly(far, ink)
    c.poly(near, ink)
    # Inner ear, shrunk toward centroid.
    def inner(tri, k=0.55):
        cx = sum(pt[0] for pt in tri) / 3
        cy = sum(pt[1] for pt in tri) / 3
        return [(cx + (x - cx) * k, cy + (yy - cy) * k) for x, yy in tri]

    c.poly(inner(far, 0.45), p["inner"])
    c.poly(inner(near, 0.48), p["inner"])

    # Forehead tabby bands (the M, seen in profile as stacked arcs).
    for i, yy in enumerate((hy - 48, hy - 28, hy - 10)):
        c.rot_ellipse(hx - 6, yy, 36 - i * 4, 8, -12, p["stripe"])

    # Cheek stripe.
    c.rot_ellipse(hx + 10, hy + 18, 28, 7, 18, p["stripe"])
    c.rot_ellipse(hx - 20, hy + 8, 22, 6, -20, p["stripe_d"])

    # Muzzle.
    if kind == "miso":
        c.ellipse([hx + 5, hy + 8, hx + hr + 8, hy + hr - 6], p["white"])
        c.ellipse([hx - 10, hy + 28, hx + 55, hy + hr + 4], p["white"])
        # White blaze up the nose.
        c.poly(
            [
                (hx + 36, hy + 8),
                (hx + 58, hy + 30),
                (hx + 70, hy + 8),
                (hx + 54, hy - 8),
            ],
            p["white"],
        )
    else:
        c.ellipse([hx + 28, hy + 18, hx + hr - 4, hy + 62], p["fur_lite"])

    # Eye.
    ex, ey = hx + 18, hy - 2
    if pose == "bump":
        ey -= 6
    ew, eh = 30, 34
    if pose == "ready":
        eh = 26
    if pose == "spike":
        eh = 28
        ew = 32
    c.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], ink)
    c.ellipse([ex - ew + 5, ey - eh + 5, ex + ew - 5, ey + eh - 5], p["eye_hi"])
    c.ellipse([ex - ew + 8, ey - eh + 8, ex + ew - 8, ey + eh - 8], p["eye"])
    c.ellipse([ex - 8, ey - 16, ex + 14, ey + 18], p["pupil"])
    c.ellipse([ex - 2, ey - 12, ex + 10, ey - 2], (255, 255, 255, 255))
    c.ellipse([ex + 6, ey + 4, ex + 12, ey + 10], (255, 255, 255, 230))

    # Nose and mouth.
    nx = hx + 62
    ny = hy + 28
    c.poly([(nx, ny), (nx + 22, ny + 8), (nx + 8, ny + 20), (nx - 6, ny + 8)], p["nose"])
    c.line([(nx + 8, ny + 18), (nx + 8, ny + 32)], ink, 3)
    c.line([(nx + 8, ny + 30), (nx - 6, ny + 38)], ink, 3)
    c.line([(nx + 8, ny + 30), (nx + 22, ny + 36)], ink, 3)

    # White chest blaze.
    if kind == "chacha":
        c.poly(
            [
                (hx - 10, y(250)),
                (hx + 18, y(270)),
                (hx + 8, y(360)),
                (hx - 28, y(340)),
                (hx - 36, y(280)),
            ],
            p["white"],
        )
        # Soft edge so it reads as a blaze, not a bib.
        c.rot_ellipse(hx - 8, y(300), 16, 40, 8, p["white"])
    else:
        c.ellipse([hx - 55, y(250), hx + 30, y(400)], p["white"])
        c.ellipse([300, y(340), 400, y(420)], p["white"])

    # White paws for Miso.
    if kind == "miso":
        if pose == "bump":
            c.ellipse([404, y(314), 456, y(348)], p["white"])
        elif pose == "spike":
            c.rot_ellipse(500, y(175), 18, 13, -20, p["white"])
        elif pose == "ready":
            c.ellipse([442, y(412), 476, y(438)], p["white"])
        else:
            c.ellipse([404, y(422), 438, y(456)], p["white"])
        # Hind paw mitten.
        if pose != "spike":
            c.ellipse([286, y(468), 328, y(498)], p["white"])
        else:
            c.ellipse([330, y(460), 366, y(488)], p["white"])

    # Stripes on haunch and back, drawn over fur but under sticker.
    c.rot_ellipse(300, y(300), 34, 8, lean + 20, p["stripe"])
    c.rot_ellipse(280, y(330), 30, 7, lean + 8, p["stripe_d"])
    c.rot_ellipse(310, y(360), 28, 7, lean - 6, p["stripe"])
    if kind == "chacha":
        c.rot_ellipse(275, y(400), 18, 7, 70, p["stripe"])
        c.rot_ellipse(268, y(430), 16, 6, 80, p["stripe_d"])

    # Ear outline redraw (so stripes don't eat ears) — ears already on top of body.
    # Whiskers after sticker so they stay thin. Stash them by drawing now in ink;
    # a modest sticker radius keeps them readable.
    c.line([(nx + 10, ny + 10), (nx + 90, ny - 6)], ink, 3)
    c.line([(nx + 10, ny + 16), (nx + 92, ny + 18)], ink, 3)
    c.line([(nx + 10, ny + 22), (nx + 84, ny + 40)], ink, 3)
    c.line([(nx - 8, ny + 12), (nx - 70, ny)], ink, 2)

    return c.finish(sticker=7)


def draw_corgi(pose):
    c = Canvas(720, 460, 2)
    ink = INK_DOG
    red = (212, 114, 52, 255)
    red_d = (184, 86, 36, 255)
    red_l = (230, 150, 96, 255)
    white = (255, 252, 248, 255)
    inner = (242, 190, 176, 255)
    nose_c = (32, 26, 24, 255)
    tongue = (224, 96, 112, 255)

    # Ground near y=430. Body is long and low. Head on the right.
    lift = {"idle": 0, "ready": 8, "bump": 0, "spike": -36}[pose]

    def y(v):
        return v + lift

    # Rump and back first (left side).
    if pose == "bump":
        # Play-bow: chest down, butt up.
        c.rot_ellipse(230, y(250), 120, 78, -18, ink)
        c.rot_ellipse(230, y(248), 108, 66, -18, red)
        c.rot_ellipse(210, y(230), 80, 36, -22, red_d)
    elif pose == "spike":
        c.rot_ellipse(250, y(250), 130, 70, -24, ink)
        c.rot_ellipse(250, y(248), 118, 58, -24, red)
        c.rot_ellipse(230, y(230), 80, 32, -28, red_d)
    else:
        back_y = y(300 if pose == "idle" else 292)
        c.rot_ellipse(250, back_y, 150, 72, -6 if pose == "idle" else -10, ink)
        c.rot_ellipse(250, back_y - 2, 138, 60, -6 if pose == "idle" else -10, red)
        c.rot_ellipse(230, back_y - 24, 100, 32, -8, red_d)

    # White rump patch — the Pembroke saddle, high on the rear.
    if pose == "bump":
        c.rot_ellipse(150, y(230), 48, 36, -20, white)
    elif pose == "spike":
        c.rot_ellipse(160, y(240), 46, 32, -30, white)
    else:
        c.rot_ellipse(145, y(285), 52, 36, -8, white)

    # Tiny tail nub, not a long tail.
    nub = (120, y(250 if pose in ("bump", "spike") else 270))
    c.ellipse([nub[0] - 22, nub[1] - 18, nub[0] + 18, nub[1] + 16], ink)
    c.ellipse([nub[0] - 16, nub[1] - 12, nub[0] + 12, nub[1] + 10], white)

    # Hind legs, very short.
    if pose == "spike":
        c.rot_ellipse(210, y(310), 28, 36, 30, ink)
        c.rot_ellipse(210, y(310), 20, 28, 30, red)
        c.ellipse([220, y(330), 270, y(365)], ink)
        c.ellipse([228, y(338), 264, y(360)], white)
    elif pose == "bump":
        c.rot_ellipse(200, y(320), 30, 40, 10, ink)
        c.rot_ellipse(200, y(320), 22, 32, 10, red)
        c.ellipse([196, y(345), 250, y(385)], ink)
        c.ellipse([204, y(354), 244, y(380)], white)
    else:
        hy = y(355)
        c.ellipse([175, hy - 10, 230, hy + 55], ink)
        c.ellipse([183, hy - 2, 222, hy + 48], red)
        c.ellipse([178, hy + 28, 236, hy + 62], ink)
        c.ellipse([186, hy + 34, 230, hy + 58], white)
        # Second hind leg peeking.
        c.ellipse([145, hy + 6, 190, hy + 58], ink)
        c.ellipse([152, hy + 12, 184, hy + 50], red_d)
        c.ellipse([148, hy + 36, 196, hy + 64], white)

    # Chest and neck (white ruff).
    if pose == "bump":
        c.rot_ellipse(390, y(330), 90, 48, 16, ink)
        c.rot_ellipse(390, y(328), 78, 38, 16, white)
        c.rot_ellipse(360, y(300), 70, 40, 20, red)
    elif pose == "spike":
        c.rot_ellipse(400, y(270), 80, 52, -10, ink)
        c.rot_ellipse(400, y(268), 68, 42, -10, red)
        c.ellipse([360, y(270), 450, y(340)], white)
    else:
        c.rot_ellipse(390, y(325), 86, 58, 8, ink)
        c.rot_ellipse(390, y(323), 74, 48, 8, red)
        c.ellipse([350, y(310), 455, y(390)], white)

    # Front legs.
    if pose == "bump":
        # Stretched forward along the ground — the receive.
        c.rot_ellipse(470, y(360), 70, 22, 8, ink)
        c.rot_ellipse(470, y(358), 60, 14, 8, white)
        c.ellipse([520, y(348), 575, y(390)], ink)
        c.ellipse([528, y(354), 568, y(384)], white)
    elif pose == "spike":
        c.rot_ellipse(470, y(230), 24, 58, -40, ink)
        c.rot_ellipse(470, y(230), 16, 48, -40, white)
        c.rot_ellipse(455, y(250), 20, 50, -10, ink)
        c.rot_ellipse(455, y(250), 13, 40, -10, white)
        c.ellipse([500, y(175), 548, y(215)], ink)
        c.ellipse([508, y(182), 540, y(208)], white)
    elif pose == "ready":
        c.ellipse([400, y(350), 445, y(420)], ink)
        c.ellipse([408, y(358), 438, y(412)], white)
        c.rot_ellipse(470, y(370), 36, 22, 20, ink)
        c.rot_ellipse(470, y(368), 28, 15, 20, white)
    else:
        c.ellipse([400, y(345), 448, y(425)], ink)
        c.ellipse([408, y(354), 440, y(418)], white)
        c.ellipse([445, y(355), 490, y(430)], ink)
        c.ellipse([452, y(364), 484, y(422)], white)

    # Head — fox shaped, big.
    if pose == "bump":
        hx, hy = 520, y(300)
    elif pose == "spike":
        hx, hy = 500, y(175)
    elif pose == "ready":
        hx, hy = 500, y(250)
    else:
        hx, hy = 490, y(255)
    c.rot_ellipse(hx, hy, 78, 64, -8, ink)
    c.rot_ellipse(hx, hy, 68, 54, -8, red)
    # White muzzle and forehead blaze.
    c.rot_ellipse(hx + 24, hy + 18, 48, 32, -8, white)
    # Blaze: narrow white stripe from the muzzle up the forehead.
    c.poly(
        [
            (hx + 8, hy + 10),
            (hx + 22, hy + 16),
            (hx + 14, hy - 46),
            (hx - 2, hy - 36),
        ],
        white,
    )

    # Ears — large, erect, rounded tips. The near ear dominates.
    if pose == "spike":
        near = [(hx - 10, hy - 20), (hx + 30, hy - 130), (hx + 85, hy - 10)]
        far = [(hx - 40, hy - 10), (hx - 20, hy - 100), (hx + 20, hy - 20)]
    elif pose == "bump":
        near = [(hx - 5, hy - 30), (hx + 35, hy - 145), (hx + 90, hy - 15)]
        far = [(hx - 48, hy - 20), (hx - 10, hy - 110), (hx + 15, hy - 25)]
    else:
        near = [(hx - 8, hy - 28), (hx + 28, hy - 150), (hx + 88, hy - 16)]
        far = [(hx - 46, hy - 16), (hx - 8, hy - 120), (hx + 18, hy - 24)]
    c.poly(far, ink)
    # fill far ear red with a slightly inset polygon
    def inset(tri, k):
        cx = sum(p_[0] for p_ in tri) / 3
        cy = sum(p_[1] for p_ in tri) / 3
        return [(cx + (x - cx) * k, cy + (yy - cy) * k) for x, yy in tri]

    c.poly(inset(far, 0.72), red_d)
    c.poly(inset(far, 0.40), inner)
    c.poly(near, ink)
    c.poly(inset(near, 0.78), red)
    c.poly(inset(near, 0.45), inner)

    # Eye.
    ex, ey = hx + 6, hy - 4
    c.ellipse([ex - 22, ey - 20, ex + 22, ey + 20], ink)
    c.ellipse([ex - 17, ey - 15, ex + 17, ey + 15], (92, 60, 36, 255))
    c.ellipse([ex - 8, ey - 10, ex + 10, ey + 12], (36, 24, 18, 255))
    c.ellipse([ex - 4, ey - 8, ex + 4, ey - 1], (255, 255, 255, 255))

    # Nose.
    c.ellipse([hx + 52, hy + 6, hx + 78, hy + 28], nose_c)
    # Mouth.
    c.line([(hx + 40, hy + 30), (hx + 62, hy + 40), (hx + 28, hy + 42)], ink, 3)
    if pose in ("idle", "ready"):
        # Small tongue, like the reference expression, not on the spike.
        c.ellipse([hx + 34, hy + 36, hx + 58, hy + 58], tongue)
        c.line([(hx + 46, hy + 38), (hx + 46, hy + 54)], (196, 70, 86, 255), 2)

    # Brow fluff / cheek.
    c.rot_ellipse(hx - 20, hy + 10, 20, 10, 20, red_l)

    return c.finish(sticker=7)


def draw_ball():
    c = Canvas(220, 220, 2)
    cx = cy = 110
    r = 78
    ink = (70, 40, 28, 255)
    c.ellipse([cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8], ink)
    c.ellipse([cx - r, cy - r, cx + r, cy + r], (248, 244, 236, 255))
    # Curved orange panels.
    orange = (232, 122, 48, 255)
    c.rot_ellipse(cx - 10, cy, 34, 70, 18, orange)
    c.rot_ellipse(cx + 28, cy + 8, 22, 62, -24, orange)
    # Re-cover with white arcs so panels read as seams, then punch seams.
    # Draw seam lines.
    c.line([(cx - 55, cy - 20), (cx - 10, cy - 55), (cx + 40, cy - 25)], ink, 5)
    c.line([(cx - 40, cy + 30), (cx + 5, cy + 5), (cx + 55, cy + 28)], ink, 5)
    c.line([(cx - 5, cy - 70), (cx - 18, cy), (cx + 8, cy + 70)], ink, 4)
    # Highlight.
    c.ellipse([cx - 48, cy - 52, cx - 10, cy - 16], (255, 255, 255, 180))
    img = c.finish(sticker=6)
    return img


def draw_net():
    # Narrow mesh with a white top tape. Bottom sits on the floor.
    w, h = 92, 400
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = 2

    def R(x0, y0, x1, y1, fill):
        d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=fill)

    def L(x0, y0, x1, y1, fill, width):
        d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=fill, width=width * s)

    ink = (48, 40, 36, 255)
    tape = (255, 252, 248, 255)
    cord = (232, 236, 238, 255)
    pole = (214, 220, 224, 255)
    # Poles.
    R(6, 8, 16, h - 2, ink)
    R(8, 10, 14, h - 4, pole)
    R(w - 16, 8, w - 6, h - 2, ink)
    R(w - 14, 10, w - 8, h - 4, pole)
    # Top tape — this is the band the ball has to clear.
    R(2, 6, w - 2, 28, ink)
    R(4, 8, w - 4, 24, tape)
    # Side tapes.
    R(16, 24, 24, h - 2, tape)
    R(w - 24, 24, w - 16, h - 2, tape)
    # Mesh cords.
    for y in range(32, h - 4, 14):
        L(24, y, w - 24, y, cord, 2)
    for x in range(28, w - 24, 10):
        L(x, 28, x, h - 4, cord, 2)
    out = im.resize((w, h), Image.Resampling.LANCZOS)
    return out


def draw_backdrop():
    W, H = 1920, 1080
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    px = im.load()
    # World rect this texture covers: x [-9.6, 9.6], y [-1.7, 9.1]
    # Floor y=0 → fraction from bottom 1.7/10.8 → pixel from top:
    floor_y = int(round((1 - (0 - (-1.7)) / 10.8) * H))  # 910

    def sky_color(x, y):
        t = y / max(1, floor_y)
        # Dusk over Victoria Harbour: warm top-left sun, teal upper sky, peach horizon.
        top = (255, 186, 140)
        mid = (126, 190, 214)
        hor = (255, 214, 176)
        if t < 0.55:
            col = mix(top, mid, t / 0.55)
        else:
            col = mix(mid, hor, (t - 0.55) / 0.45)
        # Sun glow.
        dx = (x - 280) / 420
        dy = (y - 150) / 360
        glow = max(0.0, 1 - math.sqrt(dx * dx + dy * dy))
        col = mix(col, (255, 236, 196), glow * 0.55)
        return col

    for y in range(H):
        for x in range(0, W, 2):
            if y < floor_y:
                col = sky_color(x, y)
            else:
                # Rooftop slab front. Split tint left/right so the court reads.
                u = (y - floor_y) / (H - floor_y)
                if x < W / 2:
                    base = mix((232, 176, 122), (196, 132, 86), u)
                else:
                    base = mix((168, 198, 176), (120, 154, 132), u)
                # Concrete speckle.
                if (x * 13 + y * 7) % 29 == 0:
                    base = mix(base, (255, 248, 236), 0.35)
                col = base
            px[x, y] = (*col, 255)
            if x + 1 < W:
                px[x + 1, y] = (*col, 255)

    d = ImageDraw.Draw(im)

    # Soft clouds.
    for cx, cy, rw, rh, shade in (
        (520, 120, 90, 28, 255),
        (600, 110, 70, 24, 255),
        (1480, 90, 110, 30, 250),
        (1580, 100, 80, 22, 250),
    ):
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(255, 244, 230, 90))

    # Skyline silhouettes. Bottoms sit on the waterline.
    water_top = 640
    skyline = (36, 48, 64, 255)
    window = (255, 214, 140, 255)

    def tower(x, y0, w, h, windows=True):
        d.rectangle([x, y0, x + w, water_top + 30], fill=skyline)
        if not windows:
            return
        for wy in range(int(y0) + 12, water_top, 16):
            for wx in range(int(x) + 6, int(x + w) - 6, 12):
                if (wx + wy) % 3 == 0:
                    continue
                d.rectangle([wx, wy, wx + 5, wy + 8], fill=window)

    # Left cluster — dense older blocks.
    tower(70, 470, 70, 180)
    tower(150, 430, 54, 220)
    tower(214, 500, 90, 150)
    tower(310, 450, 40, 200)
    tower(360, 490, 80, 160)

    # ICC-like slab.
    tower(860, 300, 78, 360)
    d.polygon([(860, 300), (899, 250), (938, 300)], fill=skyline)

    # Bank of China — triangular truss.
    d.polygon([(1080, water_top + 20), (1165, 280), (1250, water_top + 20)], fill=skyline)
    d.line([(1080, water_top), (1165, 280), (1250, water_top)], fill=(70, 86, 104, 255), width=4)
    d.line([(1122, 460), (1208, 460)], fill=(70, 86, 104, 255), width=3)
    d.line([(1104, 560), (1226, 560)], fill=(70, 86, 104, 255), width=3)
    d.line([(1165, 280), (1165, water_top)], fill=(70, 86, 104, 255), width=3)

    # IFC-like pair with a needle.
    tower(1360, 340, 64, 310)
    tower(1436, 390, 50, 260)
    d.polygon([(1392, 340), (1398, 250), (1404, 340)], fill=skyline)

    tower(1560, 460, 100, 190)
    tower(1680, 420, 60, 230)
    tower(1760, 500, 120, 150)

    # Harbour water.
    for y in range(water_top, 820):
        t = (y - water_top) / (820 - water_top)
        col = mix((46, 120, 156), (18, 70, 96), t)
        d.line([(0, y), (W, y)], fill=(*col, 255))
    for y in range(660, 810, 14):
        d.arc([-40, y, W + 40, y + 18], 200, 340, fill=(190, 230, 236, 110), width=2)

    # Star Ferry — white and green.
    d.polygon([(430, 760), (560, 760), (540, 800), (450, 800)], fill=(236, 240, 234, 255))
    d.rectangle([470, 730, 530, 762], fill=(236, 240, 234, 255))
    d.rectangle([478, 738, 500, 754], fill=(255, 214, 140, 255))
    d.rectangle([506, 738, 522, 754], fill=(160, 210, 220, 255))
    d.polygon([(500, 700), (500, 735), (470, 735)], fill=(40, 120, 90, 255))
    # Junk sail further down the harbour.
    d.polygon([(1500, 790), (1560, 790), (1550, 812), (1510, 812)], fill=(92, 52, 36, 255))
    d.polygon([(1524, 700), (1528, 790), (1588, 790), (1560, 730)], fill=(176, 48, 42, 255))

    # Rooftop parapet between water and the playing surface.
    d.rectangle([0, 820, W, floor_y], fill=(214, 196, 170, 255))
    d.rectangle([0, 820, W, 836], fill=(168, 148, 124, 255))
    # Railing.
    d.rectangle([0, 778, W, 788], fill=(90, 98, 104, 255))
    for x in range(20, W, 46):
        d.rectangle([x, 760, x + 6, 830], fill=(90, 98, 104, 255))

    # Laundry pole, left rooftop.
    d.line([(80, 740), (250, 700)], fill=(70, 60, 54, 255), width=4)
    for i, col in enumerate(((240, 96, 96), (96, 160, 200), (244, 200, 96), (120, 180, 140))):
        x0 = 100 + i * 36
        y0 = 732 - i * 8
        d.polygon([(x0, y0), (x0 + 28, y0 + 4), (x0 + 22, y0 + 26), (x0 - 2, y0 + 20)], fill=col + (255,))

    # Water tower.
    d.ellipse([1760, 690, 1860, 760], fill=(150, 162, 168, 255))
    d.rectangle([1798, 750, 1822, 820], fill=(120, 128, 134, 255))
    d.ellipse([1766, 696, 1854, 748], fill=(186, 196, 200, 255))

    # Neon sign.
    try:
        font = ImageFont.truetype(FONT_CJK, 42)
        font_s = ImageFont.truetype(FONT_BOLD, 18)
    except OSError:
        font = ImageFont.load_default()
        font_s = font
    sign = "海旁排球"
    d.rounded_rectangle([1280, 688, 1560, 770], radius=12, fill=(24, 28, 40, 230))
    d.text((1300, 694), sign, font=font, fill=(255, 120, 156, 255))
    d.text((1310, 742), "HARBOUR ROOFTOP", font=font_s, fill=(120, 230, 220, 255))

    # Potted plant and a paper lantern.
    d.ellipse([230, 800, 290, 830], fill=(196, 92, 64, 255))
    d.ellipse([248, 760, 276, 820], fill=(64, 140, 78, 255))
    d.ellipse([600, 742, 636, 778], fill=(216, 64, 58, 255))
    d.line([(618, 730), (618, 760)], fill=(60, 40, 30, 255), width=2)

    # String lights along the parapet.
    for i, x in enumerate(range(40, 1900, 28)):
        col = ((255, 196, 120), (255, 140, 160), (140, 220, 210))[i % 3]
        d.ellipse([x, 792, x + 8, 800], fill=col + (255,))

    # Court deck details. Floor line is the top of the slab.
    d.rectangle([0, floor_y, W, floor_y + 8], fill=(255, 250, 242, 255))
    # Baselines and centre mark, in world x.
    def wx(x):
        return int(round((x - (-9.6)) / 19.2 * W))

    for xw, label in ((-8.15, None), (8.15, None), (0, None)):
        x = wx(xw)
        d.rectangle([x - 3, floor_y, x + 3, H - 8], fill=(255, 248, 240, 230))
    # Attack-line ticks.
    for xw in (-2.4, 2.4):
        x = wx(xw)
        d.rectangle([x - 2, floor_y + 8, x + 2, floor_y + 70], fill=(255, 248, 240, 180))

    # Centre red band under the net.
    cx = wx(0)
    d.rectangle([cx - 18, floor_y + 8, cx + 18, H], fill=(176, 64, 58, 255))

    # Painted court words on the slab face.
    try:
        small = ImageFont.truetype(FONT_BOLD, 22)
    except OSError:
        small = font_s
    d.text((70, floor_y + 28), "WEST", font=small, fill=(120, 64, 32, 255))
    d.text((W - 220, floor_y + 28), "EAST", font=small, fill=(40, 80, 64, 255))
    d.text((cx - 70, floor_y + 80), "天台", font=font, fill=(255, 236, 220, 255))

    # Front lip shadow.
    d.rectangle([0, H - 18, W, H], fill=(40, 32, 28, 255))
    return im


def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "PNG")
    print(path, im.size)


def montage(paths, dest, cols=4):
    ims = [Image.open(p).convert("RGBA") for p in paths]
    cell = 280
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (40, 48, 56, 255))
    for i, im in enumerate(ims):
        im.thumbnail((cell - 16, cell - 16), Image.Resampling.LANCZOS)
        x = (i % cols) * cell + (cell - im.width) // 2
        y = (i // cols) * cell + (cell - im.height) // 2
        sheet.alpha_composite(im, (x, y))
    sheet.convert("RGB").save(dest, "JPEG", quality=90)
    print(dest)


def main():
    os.makedirs(ATH, exist_ok=True)
    os.makedirs(COURT, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    poses = ("idle", "ready", "bump", "spike")
    made = []
    for pose in poses:
        for kind in ("chacha", "miso"):
            im = draw_cat(pose, kind)
            path = os.path.join(ATH, f"{kind}_{pose}.png")
            save(im, path)
            made.append(path)
        im = draw_corgi(pose)
        path = os.path.join(ATH, f"biscuit_{pose}.png")
        save(im, path)
        made.append(path)
    save(draw_ball(), os.path.join(COURT, "ball.png"))
    save(draw_net(), os.path.join(COURT, "net.png"))
    save(draw_backdrop(), os.path.join(COURT, "backdrop.png"))
    montage(made, os.path.join(PREVIEW, "athletes.jpg"))
    # Also dump the court smaller for review.
    bg = Image.open(os.path.join(COURT, "backdrop.png"))
    bg.thumbnail((960, 540), Image.Resampling.LANCZOS)
    bg.convert("RGB").save(os.path.join(PREVIEW, "court.jpg"), "JPEG", quality=90)


if __name__ == "__main__":
    main()
