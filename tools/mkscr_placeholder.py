#!/usr/bin/env python3
"""mkscr.py - build the Mire Mare loading screen (6912-byte SCREEN$) in the
1984-85 Ultimate house style: thick interlace frame, hand-lettered title, a
night marsh scene, and the framed ULTIMATE / PLAY THE GAME badge bottom-right.
The art is drawn in Spectrum colours, then every 8x8 cell is forced to one
ink + one paper (+ one BRIGHT bit) so the result is a legal attribute screen.
Writes data/loading.scr and shots/loading_screen.png."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = '/usr/share/fonts/truetype/sand-box/google/'
def pal(i):
    lv = 0xFF if i >= 8 else 0xD7
    c = i & 7
    return ((c & 2) and lv or 0, (c & 4) and lv or 0, (c & 1) and lv or 0)
K, B, R, M, G, C, Y, W = range(8)
def br(c): return c + 8
img = Image.new('RGB', (256, 192), pal(K))
d = ImageDraw.Draw(img)
P = lambda c: pal(c)
random.seed(1985)

# ---- inner scene (cells 2..29 x 2..21 = px 16..239 x 16..175)
# stars
for _ in range(60):
    x, y = random.randrange(18, 238), random.randrange(18, 112)
    d.point((x, y), P(br(W) if random.random() < .5 else W))
# moon with the Night Mare's head in silhouette across it
mx, my, mr = 190, 86, 25
d.ellipse((mx-mr, my-mr, mx+mr, my+mr), fill=P(br(Y)))
HEAD = [(28,2),(31,9),(38,13),(44,22),(48,40),(48,52),(30,52),(29,36),(26,31),(17,31),
        (7,30),(3,27),(2,21),(6,15),(14,9),(22,6),(24,1)]
sc = 0.98
hx, hy = mx - 24*sc, my - 26*sc
d.polygon([(hx + x*sc, hy + y*sc) for x, y in HEAD], fill=P(K))
d.ellipse((hx+15*sc-1, hy+15*sc-1, hx+15*sc+1, hy+15*sc+1), fill=P(br(R)))   # burning eye
# distant fen horizon and the mere
d.rectangle((16, 120, 239, 175), fill=P(B))
for y in range(124, 176, 6):
    for x in range(16 + (y * 7) % 13, 236, 22):
        d.line((x, y, x + 8, y), fill=P(br(C)))
# moon's reflection
for i, y in enumerate(range(122, 150, 4)):
    w = 16 - i * 2
    d.line((mx - w, y, mx + w, y), fill=P(br(Y)))
# far bank of tussocks
for x in range(16, 240, 24):
    d.pieslice((x - 14, 110, x + 14, 132), 180, 360, fill=P(G))
def reed(x, base, h, lean, col):
    pts = [(x + lean * t * t, base - h * t) for t in [i / 8 for i in range(9)]]
    d.line(pts, fill=P(col), width=2)
for i, x in enumerate(range(18, 96, 7)):
    h = 36 + (i * 17) % 26
    reed(x, 176, h, (i % 3 - 1) * 6, br(G))
    if i % 3 == 0:
        tx, ty = x + (i % 3 - 1) * 6, 176 - h
        d.ellipse((tx - 2, ty - 2, tx + 3, ty + 9), fill=P(R))
# a will-o'-wisp drifting over the water
for rr, col in ((6, M), (3, br(M)), (1, br(W))):
    d.ellipse((112 - rr, 140 - rr, 112 + rr, 140 + rr), fill=P(col))
# Sabreman on a tussock, small, facing the Mare (white silhouette)
d.pieslice((118, 160, 166, 186), 180, 360, fill=P(G))
sab = [(138,166),(138,156),(135,150),(136,140),(141,136),(146,138),(148,146),(147,156),(146,166),(143,166),(142,158),(141,166)]
d.polygon(sab, fill=P(br(W)))
d.rectangle((134, 133, 151, 135), fill=P(br(W)))
d.ellipse((137, 128, 148, 138), fill=P(br(W)))
d.line([(148,146),(160,134)], fill=P(br(C)), width=1)

# ---- title, hand-lettered gothic
f = ImageFont.truetype(FONTS + 'Germania One/GermaniaOne-Regular.ttf', 40)
t = Image.new('L', (256, 70), 0); td = ImageDraw.Draw(t)
td.text((0, 0), 'Mire Mare', font=f, fill=255)
bb = t.getbbox(); t = t.crop(bb)
t = t.resize((t.width, int(t.height * 1.05)))
tx, ty = (256 - t.width) // 2, 20
mask = t.point(lambda v: 255 if v > 110 else 0)
# drop shadow / outline in magenta, letters bright white -> per-cell legal
sh = Image.new('RGB', t.size, P(br(M)))
img.paste(sh, (tx + 2, ty + 2), mask)
img.paste(Image.new('RGB', t.size, P(br(W))), (tx, ty), mask)

# ---- thick interlace frame, 2 cells wide (bright cyan knots on blue)
FR_INK, FR_PAP = br(C), B
d.rectangle((0, 0, 255, 15), fill=P(FR_PAP)); d.rectangle((0, 176, 255, 191), fill=P(FR_PAP))
d.rectangle((0, 0, 15, 191), fill=P(FR_PAP)); d.rectangle((240, 0, 255, 191), fill=P(FR_PAP))
def knot_band(horizontal, offset, length):
    # two strands weaving: sinusoids with a period of 16 px, over/under gaps
    for s in range(length):
        for strand in (0, 1):
            ph = s / 16 * 2 * math.pi + strand * math.pi
            v = 8 + 5.2 * math.sin(ph)
            over = (math.cos(ph) > 0) ^ strand
            for w in (-1, 0, 1):
                a, b = (s, offset + v + w) if horizontal else (offset + v + w, s)
                d.point((a, b), P(FR_INK))
            if not over:   # gap where this strand passes under
                a, b = (s, offset + v) if horizontal else (offset + v, s)
                if abs(math.sin(ph)) < 0.35:
                    d.point((a, b), P(FR_PAP))
knot_band(True, 0, 256); knot_band(True, 176, 256)
knot_band(False, 0, 192); knot_band(False, 240, 192)
for x0 in (0, 240):
    for y0 in (0, 176):
        d.rectangle((x0, y0, x0 + 15, y0 + 15), fill=P(FR_PAP))
        d.ellipse((x0 + 2, y0 + 2, x0 + 13, y0 + 13), outline=P(FR_INK), width=2)
        d.ellipse((x0 + 6, y0 + 6, x0 + 9, y0 + 9), fill=P(FR_INK))

# ---- ULTIMATE / PLAY THE GAME badge (black box, white outline), bottom right
bx0, by0, bx1, by1 = 168, 144, 239, 175
d.rectangle((bx0, by0, bx1, by1), fill=P(K))
d.rectangle((bx0 + 1, by0 + 1, bx1 - 1, by1 - 1), outline=P(br(W)))
fb = ImageFont.truetype(FONTS + 'Black Ops One/BlackOpsOne-Regular.ttf', 13)
fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 7)
def ctext(y, s, font, col, thr=100):
    m = Image.new('L', (80, 20), 0); ImageDraw.Draw(m).text((0, 0), s, font=font, fill=255)
    m = m.crop(m.getbbox()).point(lambda v: 255 if v > thr else 0)
    x = (bx0 + bx1 + 1 - m.width) // 2
    img.paste(Image.new('RGB', m.size, P(col)), (x, y), m)
ctext(by0 + 5, 'ULTIMATE', fb, br(G))
ctext(by0 + 21, 'PLAY THE GAME', fs, br(C), 90)

# ---- quantise to a legal Spectrum screen
cols = {pal(i): i for i in range(16)}
def nearest(rgb):
    return min(range(16), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal(i), rgb)))
px = img.load()
idx = [[cols.get(px[x, y]) if px[x, y] in cols else nearest(px[x, y]) for x in range(256)] for y in range(192)]
bitmap = bytearray(6144); attrs = bytearray(768)
out = Image.new('RGB', (256, 192)); op = out.load()
for cy in range(24):
    for cx in range(32):
        cnt = {}
        for y in range(cy*8, cy*8+8):
            for x in range(cx*8, cx*8+8):
                c = idx[y][x]; cnt[c] = cnt.get(c, 0) + 1
        bright = 1 if sum(n for c, n in cnt.items() if c >= 8 and c != 8) >= \
                      sum(n for c, n in cnt.items() if 0 < c < 8) else 0
        cnt7 = {}
        for c, n in cnt.items(): cnt7[c & 7] = cnt7.get(c & 7, 0) + n
        order = sorted(cnt7, key=lambda c: -cnt7[c])
        paper = order[0]; ink = order[1] if len(order) > 1 else order[0]
        # keep black as paper where it is present, Ultimate style
        if 0 in order[:2] and paper != 0: ink, paper = paper, 0
        a = (bright << 6) | (paper << 3) | ink
        attrs[cy*32 + cx] = a
        ip, pp = pal(ink + 8*bright), pal(paper + 8*bright)
        for y in range(cy*8, cy*8+8):
            v = 0
            for x in range(cx*8, cx*8+8):
                c = idx[y][x] & 7
                if c == ink and ink != paper: on = 1
                elif c == paper: on = 0
                else:
                    rgb = pal(idx[y][x])
                    on = sum((a1 - b1)**2 for a1, b1 in zip(rgb, ip)) < sum((a1 - b1)**2 for a1, b1 in zip(rgb, pp))
                v = (v << 1) | on
                op[x, y] = ip if on else pp
            addr = ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | cx
            bitmap[addr] = v
scr = bytes(bitmap + attrs); assert len(scr) == 6912
open(os.path.join(ROOT, 'data/loading.scr'), 'wb').write(scr)
os.makedirs(os.path.join(ROOT, 'shots'), exist_ok=True)
out.resize((768, 576), Image.NEAREST).save(os.path.join(ROOT, 'shots/loading_screen.png'))
print('wrote data/loading.scr (6912 bytes) and shots/loading_screen.png')
