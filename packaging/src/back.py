"""Box back (135x195), long spine (195x25), short spine (135x25); 3 mm bleed, 300 dpi. Plus a flat wrap preview."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from text import *
from front import matte_black, painting, framed, build_front, TW, TH, BL
import numpy as np
WHITE = (242, 242, 236); DEPTH = 25
def vignette(img, feather):
    w, h = img.size; m = Image.new('L', (w, h)); ImageDraw.Draw(m).ellipse((feather, feather, w - feather, h - feather), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(feather * .8)); out = Image.new('RGBA', (w, h)); out.paste(img, (0, 0), m); return out
def build_back():
    W, H = mm(TW + 2 * BL), mm(TH + 2 * BL); o = mm(BL); c = matte_black(W, H, 2); d = ImageDraw.Draw(c)
    f = font('serifb', mm(5.2)); s = '48K SINCLAIR ZX SPECTRUM'
    d.text(((W - d.textlength(s, font=f)) / 2, o + mm(5)), s, font=f, fill=WHITE)
    # the Mare's head, cut from the painting and vignetted into the black
    src = Image.open('src/cover_c.jpg').convert('RGB').crop((230, 150, 560, 480))
    src = src.resize((mm(80), mm(80)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 50, 2))
    v = vignette(src, mm(9)); c.paste(v, ((W - v.width) // 2, o + mm(14)), v)
    y = o + mm(97)
    fb = font('serifb', mm(4.6)); fi = font('serifi', mm(4.6))
    for i, p in enumerate(BACK_BLURB):
        y = centred_block(d, o + mm(14), W - o - mm(14), y, [p], fb if i else fi, gap=.7)
    t = title_logo(mm(14), two_line=False); c.paste(t, ((W - t.width) // 2, int(y) + mm(1)), t)
    b = badge(mm(50)); c.paste(b, ((W - b.width) // 2, o + mm(TH - 19) - b.height), b)
    fs = font('serif', mm(2.6))
    centred_block(d, o + mm(10), W - o - mm(10), o + mm(TH - 16), ["MIRE MARE \u00a9 1985 Ashby Computers & Graphics Ltd. All rights reserved.",
                  "ULTIMATE PLAY THE GAME, The Green, Ashby de la Zouch, Leicestershire.   " + CAT], fs, gap=.1)
    return c
def build_spine(length):
    W, H = mm(length + 2 * BL), mm(DEPTH + 2 * BL); o = mm(BL); c = matte_black(W, H, 3); d = ImageDraw.Draw(c)
    t = title_logo(mm(DEPTH - 7), two_line=False); c.paste(t, (o + mm(8), (H - t.height) // 2), t)
    b = badge(mm(40)); c.paste(b, (W - o - mm(6) - b.width, (H - b.height) // 2), b)
    if length > 150:
        f = font('serifb', mm(4)); s = '48K SINCLAIR ZX SPECTRUM'
        x = o + mm(8) + t.width + (W - o - mm(6) - b.width - o - mm(8) - t.width - d.textlength(s, font=f)) / 2
        d.text((x, (H - f.size) / 2 - mm(.6)), s, font=f, fill=WHITE)
    return c
if __name__ == '__main__':
    bk = build_back(); bk.save('out/02_box_back.png', dpi=(300, 300))
    sl = build_spine(TH); sl.save('out/02_box_spine_long.png', dpi=(300, 300))
    ss = build_spine(TW); ss.save('out/02_box_spine_short.png', dpi=(300, 300))
    fr = Image.open('out/01_box_front.png'); o = mm(BL)
    # flat wrap preview (trimmed): spine | front | spine | back
    tr = lambda im: im.crop((o, o, im.width - o, im.height - o))
    sv = tr(sl).rotate(90, expand=True); F = tr(fr); B = tr(bk)
    wrap_ = Image.new('RGB', (sv.width * 2 + F.width + B.width, F.height), 'black'); x = 0
    for im in (sv, F, sv, B): wrap_.paste(im, (x, 0)); x += im.width
    wrap_.save('out/02_box_wrap_preview.png', dpi=(300, 300))
    wrap_.resize((wrap_.width // 5, wrap_.height // 5)).save('work/prev_wrap.png')
