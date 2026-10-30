"""Spectrum-native loading screen from the final cover concept.
Layout after Nathan's refs (Knight Lore / Sabre Wulf): thick geometric frame, the cover painting
converted cell-by-cell on the left, hand-lettered MIRE MARE in a mist cloud on the right, the
ULTIMATE / PLAY THE GAME badge bottom-right. Every 8x8 cell = 1 ink + 1 paper + 1 BRIGHT bit.
Writes ../art/loading_final.scr (installed by tools/mkscr.py into data/loading.scr) + previews."""
import sys, os, math; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from lib import title_logo, font, dilate, G
HERE = os.path.dirname(os.path.abspath(__file__)); PK = os.path.dirname(HERE); ROOT = os.path.dirname(PK)
def pal(i):
    lv = 0xFF if i >= 8 else 0xD7; c = i & 7
    return ((c & 2) and lv or 0, (c & 4) and lv or 0, (c & 1) and lv or 0)
K, B, R, M, Gr, C, Y, W = range(8)
BAYER = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                  [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                  [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64 + 1 / 128
# --- screen model: per cell ink, paper, bright and an 8x8 bitmap
ink = np.zeros((24, 32), int); pap = np.zeros((24, 32), int); bri = np.zeros((24, 32), int)
bits = np.zeros((192, 256), bool)
def convert_region(rgb, cx0, cy0, gamma=1.3):
    """Ultimate-style conversion: paper always black; one ink per cell chosen by the cell's hue
    (white for pale areas, a hue for saturated ones, red where the Mare's eyes burn); the ink
    coverage follows luminance through an ordered dither, giving an engraved look."""
    h, w, _ = rgb.shape; lum = rgb.mean(-1) / 255.0
    for cy in range(h // 8):
        for cx in range(w // 8):
            blk = rgb[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8]; L = lum[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8]
            wgt = (L ** 2)[..., None]; mc = (blk * wgt).sum((0, 1)) / max(wgt.sum(), 1e-6)
            redm = (blk[..., 0] > 235) & (blk[..., 1] < 70) & (blk[..., 2] < 70); red = redm.sum()
            sat = (mc.max() - mc.min()) / max(mc.max(), 1)
            if red >= 2: col = R
            elif sat < .4: col = W
            else:
                best = None
                for i in (B, R, M, Gr, C, Y):
                    P = np.array(pal(i + 8), float); cn = mc / (np.linalg.norm(mc) + 1e-6); pn = P / np.linalg.norm(P)
                    e = 1 - (cn * pn).sum()
                    if best is None or e < best[0]: best = (e, i)
                col = best[1]
            bright = 1 if L.mean() > .28 or col == R else 0
            P = np.array(pal(col + 8 * bright), float)
            t = np.clip((L ** gamma) * (255 * 3 / max(P.sum(), 1) if col == W else 1.1), 0, 1)
            on = t > BAYER
            if col == R: on = redm | ((L > .45) & (BAYER < .4))
            Y_, X_ = cy0 + cy, cx0 + cx
            pap[Y_, X_], ink[Y_, X_], bri[Y_, X_] = K, col, bright
            bits[Y_ * 8:Y_ * 8 + 8, X_ * 8:X_ * 8 + 8] = on
def set_cell(cx, cy, i, p, b): ink[cy, cx], pap[cy, cx], bri[cy, cx] = i, p, b
def draw_mask(mask, x0, y0, on=True):
    """write a 1-bit PIL 'L' mask into the bitmap (attributes set separately)"""
    a = np.array(mask) > 127; h, w = a.shape
    sub = bits[y0:y0 + h, x0:x0 + w]; sub[a[:sub.shape[0], :sub.shape[1]]] = on
# ---------------- 1. frame: 2 cells thick, bevelled geometric double band (bright cyan on blue)
fr = Image.new('L', (256, 192)); d = ImageDraw.Draw(fr)
for r, wdt in ((1, 2), (6, 1), (9, 1), (14, 2)):
    d.rectangle((r, r, 255 - r, 191 - r), outline=255, width=wdt)
for x in range(16, 240, 8):   # chevron "bridle stitching" between the rules
    d.line((x, 7, x + 4, 7 + 2), fill=255); d.line((x + 4, 9, x + 8, 7), fill=255)
    d.line((x, 184, x + 4, 182), fill=255); d.line((x + 4, 182, x + 8, 184), fill=255)
for y in range(16, 176, 8):
    d.line((7, y, 9, y + 4), fill=255); d.line((9, y + 4, 7, y + 8), fill=255)
    d.line((248, y, 246, y + 4), fill=255); d.line((246, y + 4, 248, y + 8), fill=255)
for x0, y0 in ((0, 0), (240, 0), (0, 176), (240, 176)):   # roundel studs (bridle rivets) at corners
    d.rectangle((x0, y0, x0 + 15, y0 + 15), fill=0); d.rectangle((x0 + 1, y0 + 1, x0 + 14, y0 + 14), outline=255, width=2)
    d.ellipse((x0 + 4, y0 + 4, x0 + 11, y0 + 11), outline=255, width=2); d.point((x0 + 7, y0 + 7), 255); d.point((x0 + 8, y0 + 8), 255)
frm = np.array(fr) > 0
for cy in range(24):
    for cx in range(32):
        if cx < 2 or cx > 29 or cy < 2 or cy > 21:
            corner = (cx < 2 or cx > 29) and (cy < 2 or cy > 21)
            set_cell(cx, cy, Y if corner else C, B if not corner else R, 1)
            bits[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8] = frm[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8]
# ---------------- 2. painting, left: cells 2..16 (120 px) x 2..21 (160 px)
p = Image.open(os.path.join(PK, 'src/cover_c.jpg')).convert('RGB')
p = p.crop((40, 60, 768 - 40, 60 + int((768 - 80) * 160 / 120)))
p = ImageEnhance.Color(p).enhance(1.6); p = ImageEnhance.Contrast(p).enhance(1.4)
p = p.resize((120, 160), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1, 120, 0))
convert_region(np.array(p, float), 2, 2)
# Sabreman himself, from the game's own sprite sheet (sab_hit_r), white on black, cell-aligned
def sprite(name):
    L = open(os.path.join(ROOT, 'art/sprites.txt')).read().split('\n'); i = L.index(next(l for l in L if l.startswith('SPRITE ' + name + ' ')))
    w, h = map(int, L[i].split()[2].split('x')); return np.array([[c == '#' for c in L[i + 1 + r][:w].ljust(w, '.')] for r in range(h)])
spr = sprite('sab_hit_r'); SX, SY = 56, 120
from scipy import ndimage as _nd
key = _nd.binary_dilation(spr, iterations=1)
for cy in range(SY // 8, SY // 8 + 3):
    for cx in range(SX // 8, SX // 8 + 3):
        set_cell(cx, cy, W, K, 1)
sub = bits[SY:SY + 24, SX:SX + 24]; sub[key] = False; sub[spr] = True
# ---------------- 3. right panel: mist cloud + title, cells 17..29 x 2..21
# title lettering at pixel scale: white keyline, interior shows the cloud's paper colour
TF = font('title', 40)
lm = Image.new('L', (256, 192)); ld = ImageDraw.Draw(lm)
def place(word, y):
    t = Image.new('L', (200, 60)); ImageDraw.Draw(t).text((0, 0), word, font=TF, fill=255); t = t.crop(t.getbbox())
    t = t.resize((min(t.width, 94), 34)).point(lambda v: 255 if v > 110 else 0)
    return t
t1, t2 = place('Mire', 0), place('Mare', 0)
lm.paste(t1, (142, 28), t1); lm.paste(t2, (152 + (84 - t2.width), 70), t2)
# mire drips under the second word
for x in (160, 178, 197, 216, 229):
    col = np.nonzero(np.array(lm)[:, x] > 0)[0]
    if len(col): yb = col.max(); ld.line((x, yb, x, yb + 4 + x % 5), fill=255); ld.point((x + 1, yb + 4 + x % 5), 255)
L_ = np.array(lm) > 0
from scipy import ndimage
outer = ndimage.binary_dilation(L_, iterations=1)
ring = outer & ~ndimage.binary_erosion(L_, iterations=1)   # 2-px white keyline, hollow letters
tmask = ring
# cloud bands (cell-aligned, Knight Lore style): magenta core, blue ring, cyan edge
core = ndimage.binary_dilation(outer, iterations=7)
cyc = np.zeros((24, 32), int)
for cy in range(2, 22):
    for cx in range(17, 30):
        f = core[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8].mean(); cyc[cy, cx] = 3 if f > .45 else 0
for _ in range(2):
    nb = ndimage.binary_dilation(cyc > 0) & (cyc == 0); cyc[nb] = 2 if _ == 0 else 1
cyc[:, :17] = 0; cyc[:, 30:] = 0; cyc[:2] = 0; cyc[22:] = 0; cyc[17:, 19:] = 0
import random; rnd = random.Random(1985)
for cy in range(2, 22):
    for cx in range(17, 30):
        blk = (slice(cy * 8, cy * 8 + 8), slice(cx * 8, cx * 8 + 8))
        k = cyc[cy, cx]
        if k == 3: set_cell(cx, cy, W, M, 1); bits[blk] = tmask[blk]
        elif k == 2: set_cell(cx, cy, W if tmask[blk].any() else C, B, 1); bits[blk] = tmask[blk] | (~tmask[blk] & (BAYER < .12) if False else tmask[blk])
        elif k == 1: set_cell(cx, cy, W, K, 1); bits[blk] = False
        else: set_cell(cx, cy, W, K, 1); bits[blk] = False
for _ in range(26):   # stars in the black sky
    x, y = rnd.randrange(138, 238), rnd.randrange(18, 132); cx, cy = x // 8, y // 8
    if cyc[cy, cx] == 0 and pap[cy, cx] == K and ink[cy, cx] == W:
        bits[y, x] = True
        if rnd.random() < .35:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx) // 8 == cx and (y + dy) // 8 == cy: bits[y + dy, x + dx] = True
# reeds and a wisp above the badge (green ink on black, wisp bright cyan)
rd = Image.new('L', (256, 192)); r_ = ImageDraw.Draw(rd)
for i, x in enumerate(range(140, 238, 6)):
    h = 14 + (i * 11) % 16; lean = (i % 3 - 1) * 3
    r_.line([(x, 135), (x + lean, 135 - h)], fill=255, width=1)
    if i % 3 == 0: r_.ellipse((x + lean - 1, 135 - h - 1, x + lean + 2, 135 - h + 6), fill=255)
rm = np.array(rd) > 0
for cy in range(13, 17):
    for cx in range(17, 30):
        blk = (slice(cy * 8, cy * 8 + 8), slice(cx * 8, cx * 8 + 8))
        if rm[blk].any() and pap[cy, cx] == K: set_cell(cx, cy, Gr, K, 1 if cy > 14 else 0); bits[blk] = rm[blk]
# ---------------- 4. badge, bottom-right: cells 19..29 x 17..21 (88x40 px)
bx0, by0, bx1, by1 = 152, 138, 239, 175
for cy in range(17, 22):
    for cx in range(19, 30): set_cell(cx, cy, W, K, 1); bits[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8] = False
bd = Image.new('L', (256, 192)); bdd = ImageDraw.Draw(bd)
bdd.rectangle((bx0 + 1, by0 + 1, bx1 - 1, by1 - 1), outline=255)
fb = ImageFont.truetype(G + 'Russo One/RussoOne-Regular.ttf', 16)
m = Image.new('L', (120, 24)); ImageDraw.Draw(m).text((0, 0), 'ULTIMATE', font=fb, fill=255); m = m.crop(m.getbbox()).resize((78, 13)).point(lambda v: 255 if v > 110 else 0)
bd.paste(m, ((bx0 + bx1 + 1 - 78) // 2, by0 + 5), m)
fp = ImageFont.truetype(G + 'Russo One/RussoOne-Regular.ttf', 9)
m2 = Image.new('L', (120, 16)); ImageDraw.Draw(m2).text((0, 0), 'PLAY THE GAME', font=fp, fill=255); m2 = m2.crop(m2.getbbox()).resize((72, 7)).point(lambda v: 255 if v > 100 else 0)
bd.paste(m2, ((bx0 + bx1 + 1 - 72) // 2, by0 + 24), m2)
bm = np.array(bd) > 0
for cy in range(17, 22):
    for cx in range(19, 30):
        blk = (slice(cy * 8, cy * 8 + 8), slice(cx * 8, cx * 8 + 8)); bits[blk] |= bm[blk]
# chrome colour per character row, like the real badge: green top, cyan lower, white rule
for cx in range(19, 30):
    set_cell(cx, 17, W, K, 1)
    set_cell(cx, 18, Gr, K, 1); set_cell(cx, 19, Gr, K, 1)   # ULTIMATE rows 143..156 -> green
    set_cell(cx, 20, C, K, 1); set_cell(cx, 21, W, K, 1)
# rows 17 and 21 contain the white outline; ULTIMATE spans rows 143-155 = cells 17(.875)-19; fix the top cell
# (the box outline at y=139 shares cell row 17 with the top of ULTIMATE -> keep it white there)
# ---------------- 5. write SCREEN$
bitmap = bytearray(6144); attrs = bytearray(768)
for y in range(192):
    for cx in range(32):
        v = 0
        for x in range(8): v = (v << 1) | int(bits[y, cx * 8 + x])
        bitmap[((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | cx] = v
for cy in range(24):
    for cx in range(32): attrs[cy * 32 + cx] = (bri[cy, cx] << 6) | (pap[cy, cx] << 3) | ink[cy, cx]
scr = bytes(bitmap + attrs); assert len(scr) == 6912
open(os.path.join(ROOT, 'art/loading_final.scr'), 'wb').write(scr)
# render from the bytes (proves the file itself is right)
def render(scr):
    im = Image.new('RGB', (256, 192)); px = im.load()
    for y in range(192):
        for cx in range(32):
            v = scr[((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | cx]; at = scr[6144 + (y // 8) * 32 + cx]
            b = (at >> 6) & 1; i_, p_ = pal((at & 7) + 8 * b), pal(((at >> 3) & 7) + 8 * b)
            for x in range(8): px[cx * 8 + x, y] = i_ if v & (0x80 >> x) else p_
    return im
im = render(scr)
im.save(os.path.join(PK, 'out/06_loading_screen_256x192.png'))
im.resize((768, 576), Image.NEAREST).save(os.path.join(PK, 'out/06_loading_screen_x3.png'))
# legality check: max distinct colours per cell
mx = max(len(set(im.crop((cx * 8, cy * 8, cx * 8 + 8, cy * 8 + 8)).getdata())) for cy in range(24) for cx in range(32))
print('art/loading_final.scr written; max colours per cell =', mx)
