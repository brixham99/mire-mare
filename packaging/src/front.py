"""Box front: 135 x 195 mm trim + 3 mm bleed, 300 dpi."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import numpy as np
TW, TH, BL = 135, 195, 3
def matte_black(w, h, seed=1):
    rnd = np.random.default_rng(seed)
    n = rnd.normal(0, 1, (h // 2 + 1, w // 2 + 1))
    img = Image.fromarray(np.clip(16 + n * 4, 0, 255).astype('uint8')).resize((w, h)).filter(ImageFilter.GaussianBlur(1.2))
    return Image.merge('RGB', (img, img, img))
def painting(w, h, src='src/cover_c.jpg', focus=0.5):
    p = Image.open(src).convert('RGB')
    r = max(w / p.width, h / p.height)
    p = p.resize((int(p.width * r) + 1, int(p.height * r) + 1), Image.LANCZOS)
    x = (p.width - w) // 2; y = int((p.height - h) * focus)
    p = p.crop((x, y, x + w, y + h)).filter(ImageFilter.UnsharpMask(3, 60, 2))
    g = np.random.default_rng(5).normal(0, 3, (h, w, 1))  # painted-board grain hides upscale
    return Image.fromarray(np.clip(np.array(p) + g, 0, 255).astype('uint8'))
def framed(img, rad, gold=True):
    w, h = img.size; m = Image.new('L', (w, h)); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), rad, fill=255)
    out = Image.new('RGBA', (w, h)); out.paste(img, (0, 0), m)
    d = ImageDraw.Draw(out); lw = mm(.8)
    col = (205, 160, 70) if gold else (230, 230, 230)
    d.rounded_rectangle((lw, lw, w - lw - 1, h - lw - 1), rad, outline=col, width=lw)
    d.rounded_rectangle((mm(2), mm(2), w - mm(2) - 1, h - mm(2) - 1), rad - mm(1.5), outline=(120, 40, 140), width=mm(.35))
    return out
def build_front(trim_only=False):
    W, H = mm(TW + 2 * BL), mm(TH + 2 * BL); o = mm(BL)
    c = matte_black(W, H)
    d = ImageDraw.Draw(c)
    f = font('serifb', mm(5.2)); s = '48K SINCLAIR ZX SPECTRUM'
    tw = d.textlength(s, font=f); d.text(((W - tw) / 2, o + mm(5)), s, font=f, fill=(245, 245, 245))
    pw, ph = mm(113), mm(122)
    pic = framed(painting(pw, ph, focus=.55), mm(6))
    c.paste(pic, ((W - pw) // 2, o + mm(44)), pic)
    t = title_logo(mm(46))
    c.paste(t, ((W - t.width) // 2, o + mm(13)), t)
    b = badge(mm(88))
    c.paste(b, ((W - b.width) // 2, o + mm(TH - 6) - b.height), b)
    return c
if __name__ == '__main__':
    c = build_front()
    c.save('out/01_box_front.png', dpi=(300, 300))
    c.resize((c.width // 4, c.height // 4)).save('work/prev_front.png')
