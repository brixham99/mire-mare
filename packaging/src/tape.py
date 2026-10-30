"""Cassette labels, side A and B: 102 x 64 mm, 2 mm bleed, 300 dpi, one-colour white print on a solid ground."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from text import *
GROUND = (22, 104, 74)   # mire green, in the solid-colour run of SW red / KL orange / UW maroon
W_MM, H_MM, BL = 102, 64, 2
WH = (250, 250, 245)
def window_mask(W, H, o):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    x0, x1 = o + mm(22), o + mm(W_MM - 22); y0, y1 = o + mm(23), o + mm(41)
    d.rounded_rectangle((x0, y0, x1, y1), radius=mm(9), fill=255)
    return m
def ruled_badge(width, ground):
    """one-colour ULTIMATE / PLAY THE GAME box as printed on the tape"""
    S = width * 2; H = int(S * .36); im = Image.new('RGBA', (S, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lw = int(S * .018); d.rectangle((0, 0, S - 1, H - 1), fill=WH); d.rectangle((lw, lw, S - lw - 1, H - lw - 1), fill=ground)
    d.rectangle((lw * 2, lw * 2, S - lw * 2 - 1, H - lw * 2 - 1), outline=WH, width=max(2, lw // 2))
    f = font('badge', int(H * .5)); t = 'ULTIMATE'; tw = d.textlength(t, font=f)
    tt = Image.new('L', (int(tw) + 10, int(f.size * 1.3))); ImageDraw.Draw(tt).text((0, 0), t, font=f, fill=255); tt = tt.crop(tt.getbbox())
    tt = tt.resize((int(S * .82), int(H * .42))); im.paste(WH, ((S - tt.width) // 2, int(H * .13)), tt)
    f2 = font('badge', int(H * .2)); t2 = 'PLAY THE GAME'
    p = Image.new('L', (S, int(f2.size * 1.4))); ImageDraw.Draw(p).text((0, 0), t2, font=f2, fill=255); p = p.crop(p.getbbox()); p = p.resize((int(S * .7), p.height))
    im.paste(WH, ((S - p.width) // 2, int(H * .64)), p)
    return im.resize((width, int(H * width / S)), Image.LANCZOS)
def label(side):
    W, H = mm(W_MM + 2 * BL), mm(H_MM + 2 * BL); o = mm(BL)
    c = Image.new('RGBA', (W, H), GROUND + (255,)); d = ImageDraw.Draw(c)
    b = ruled_badge(mm(44), GROUND); c.paste(b, ((W - b.width) // 2, o + mm(5)), b)
    d.text(((W + b.width) // 2 + mm(.8), o + mm(4)), '\u00a9', font=font('sans', mm(3.4)), fill=WH)
    t = title_logo(mm(14), mono=WH)
    for x in (o + mm(4), W - o - mm(4) - t.width): c.paste(t, (x, o + mm(4)), t)
    # corner stripes
    for k in range(5):
        dx = mm(2.2) * k
        d.polygon([(o + mm(3) + dx, o + mm(48)), (o + mm(4.3) + dx, o + mm(48)), (o + mm(18), o + mm(60) - dx), (o + mm(18), o + mm(61.3) - dx)], fill=WH)
        d.polygon([(W - o - mm(3) - dx, o + mm(48)), (W - o - mm(4.3) - dx, o + mm(48)), (W - o - mm(18), o + mm(60) - dx), (W - o - mm(18), o + mm(61.3) - dx)], fill=WH)
    f = font('serifb', mm(3.6)); s = '48K SINCLAIR ZX SPECTRUM'
    d.text(((W - d.textlength(s, font=f)) / 2, o + mm(45)), s, font=f, fill=WH)
    fs = font('sans', mm(2.4))
    for i, s in enumerate(['MIRE MARE \u00a9 Copyright 1985 Ashby Computers & Graphics Ltd.', '- All Rights Reserved -']):
        d.text(((W - d.textlength(s, font=fs)) / 2, o + mm(51) + i * mm(3.2)), s, font=fs, fill=WH)
    fside = font('badge', mm(7)); d.text((o + mm(10), o + mm(28)), side, font=fside, fill=WH)
    d.text((W - o - mm(15), o + mm(28)), side, font=fside, fill=WH)
    c.paste((0, 0, 0, 0), (0, 0), window_mask(W, H, o))   # spindle window cut out
    return c
if __name__ == '__main__':
    for s in 'AB':
        im = label(s); im.save(f'out/04_tape_label_side{s}.png', dpi=(300, 300))
    a = Image.open('out/04_tape_label_sideA.png'); b = Image.open('out/04_tape_label_sideB.png')
    p = Image.new('RGB', (a.width * 2 + 40, a.height), (60, 60, 60)); p.paste(a, (0, 0), a); p.paste(b, (a.width + 40, 0), b)
    p.resize((p.width // 3, p.height // 3)).save('work/prev_tape1.png')
