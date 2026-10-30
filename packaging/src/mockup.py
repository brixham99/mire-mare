"""Photo-style mock-up: big box standing (front + long spine in perspective), opened inlay lying flat, cassette in its case. Composited."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
W, H = 3600, 2400
def coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()
def quad(img, dst):
    img = img.convert('RGBA'); w, h = img.size
    return img.transform((W, H), Image.PERSPECTIVE, coeffs(dst, [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)
def crop_bleed(im, b): return im.crop((b, b, im.width - b, im.height - b))
def shadow(layer, off=(30, 30), blur=40, op=170):
    a = layer.split()[3].point(lambda v: op if v > 0 else 0)
    s = Image.new('RGBA', (W, H), (0, 0, 0, 0)); s.putalpha(a)
    s = s.transform((W, H), Image.AFFINE, (1, 0, -off[0], 0, 1, -off[1])).filter(ImageFilter.GaussianBlur(blur)); return s
def shade(layer, k):
    r, g, b, a = layer.split(); rgb = ImageEnhance.Brightness(Image.merge('RGB', (r, g, b))).enhance(k); return Image.merge('RGBA', (*rgb.split(), a))
def table():
    rng = np.random.default_rng(3)
    y, x = np.mgrid[0:H, 0:W]
    n = np.asarray(Image.fromarray((rng.random((H // 8, W // 8)) * 255).astype('uint8')).resize((W, H), Image.BICUBIC), float) / 255
    base = np.stack([46 + 8 * n, 44 + 8 * n, 50 + 9 * n], -1)   # dark grey-blue desk mat
    d = np.hypot((x - W * .45) / W, (y - H * .35) / H); light = np.clip(1.25 - d * 1.5, .25, 1.25)[..., None]
    base = base * light + rng.normal(0, 3, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype('uint8')).convert('RGBA')
def cassette(label):
    # 100 x 63 mm case at ~12 px/mm, smoked plastic, label inset
    s = 12; cw, ch = 110 * s, 70 * s
    c = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=(28, 30, 34, 255), outline=(90, 95, 105, 255), width=6)
    d.rounded_rectangle((14, 14, cw - 15, ch - 15), 30, outline=(60, 64, 72, 255), width=3)
    lab = label.resize((96 * s, 60 * s), Image.LANCZOS)
    # reels and tape visible through the label window
    win = Image.new('RGBA', lab.size, (0, 0, 0, 0)); wd = ImageDraw.Draw(win)
    wd.rectangle((0, 0, lab.width, lab.height), fill=(40, 30, 26, 255))
    for cx in (lab.width * .33, lab.width * .67):
        cy = lab.height * .52
        wd.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), fill=(58, 40, 30, 255))
        wd.ellipse((cx - 45, cy - 45, cx + 45, cy + 45), fill=(230, 230, 225, 255))
        for k in range(6):
            a = k * np.pi / 3; wd.line((cx, cy, cx + 38 * np.cos(a), cy + 38 * np.sin(a)), fill=(120, 120, 120, 255), width=8)
    win.alpha_composite(lab); c.alpha_composite(win, (7 * s, 5 * s))
    # gloss over the shell
    g = Image.new('RGBA', c.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.polygon([(0, 0), (cw * .55, 0), (cw * .25, ch), (0, ch)], fill=(255, 255, 255, 18))
    c.alpha_composite(Image.composite(g, Image.new('RGBA', c.size, (0, 0, 0, 0)), c.split()[3]))
    return c
def main():
    sc = table()
    out = 'out/'
    front = crop_bleed(Image.open(out + '01_box_front.png'), 35)
    spine = crop_bleed(Image.open(out + '02_box_spine_long.png'), 35).rotate(90, expand=True)  # vertical, title reads bottom-to-top
    inlay = crop_bleed(Image.open(out + '03_inlay_outer.png'), 35)
    label = crop_bleed(Image.open(out + '04_tape_label_sideA.png'), 24)
    # 1. inlay lying flat, behind, receding (trapezoid)
    il = quad(inlay, [(260, 1300), (3420, 1240), (3560, 2250), (60, 2330)])
    sc.alpha_composite(shadow(il, (10, 18), 18, 140)); sc.alpha_composite(il)
    # 2. box standing upright: spine (left, angled) + front
    fx0, fy0, fx1, fy1 = 1130, 140, 2080, 1760
    fr = quad(front, [(fx0, fy0), (fx1, fy0 + 40), (fx1, fy1 - 25), (fx0, fy1)])
    sp = quad(spine, [(fx0 - 150, fy0 - 50), (fx0, fy0), (fx0, fy1), (fx0 - 150, fy1 - 40)])
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0)); base.alpha_composite(fr); base.alpha_composite(sp)
    sc.alpha_composite(shadow(base, (90, 20), 50, 190))
    sc.alpha_composite(shade(sp, .62)); sc.alpha_composite(fr)
    hl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(hl).line([(fx0, fy0), (fx0, fy1)], fill=(255, 255, 255, 70), width=4); sc.alpha_composite(hl)
    # 3. cassette lying in front, rotated
    cas = cassette(label).rotate(-11, expand=True, resample=Image.BICUBIC)
    cas = cas.resize((int(cas.width * .92), int(cas.height * .92)), Image.LANCZOS)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.alpha_composite(cas, (2180, 1420))
    sc.alpha_composite(shadow(lay, (25, 30), 30, 180)); sc.alpha_composite(lay)
    # overall photo feel: slight vignette and softness
    y, x = np.mgrid[0:H, 0:W]; v = np.clip(1.15 - np.hypot((x - W / 2) / W, (y - H / 2) / H) * 1.1, .55, 1)[..., None]
    a = np.asarray(sc.convert('RGB'), float) * v
    img = Image.fromarray(np.clip(a, 0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(.6))
    img.save(out + '07_mockup.png', dpi=(300, 300)); img.resize((W // 4, H // 4), Image.LANCZOS).save('work/prev_mock1.png')
if __name__ == '__main__': main()
