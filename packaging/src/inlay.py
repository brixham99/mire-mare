"""Fold-out inlay (big-box insert card), both sides. 412 x 180 mm trim, 3 mm bleed, 300 dpi.
Outer: [credits 36][spine 32][front 117][controls 115][loading 112]  Inner: 3 x 137.3 (prose+riddle | prose | features)"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from text import *
from front import matte_black, painting, framed
TW, TH, BL = 412, 180, 3
WHITE = (242, 242, 236)
def canvas():
    W, H = mm(TW + 2 * BL), mm(TH + 2 * BL)
    c = Image.new('RGB', (W, H), (8, 8, 8)); return c, ImageDraw.Draw(c), mm(BL)
def folds(d, o, xs, H):
    for x in xs:  # fold marks in the bleed only
        X = o + mm(x); d.line((X, 0, X, o - mm(.5)), fill=(90, 90, 90), width=2); d.line((X, H - o + mm(.5), X, H), fill=(90, 90, 90), width=2)
def outer():
    c, d, o = canvas(); H = c.height
    xs = [0, 36, 68, 185, 300, 412]
    X = [o + mm(v) for v in xs]
    top, bot = o + mm(8), o + mm(TH - 8)
    # credits strip (rotated text)
    strip = Image.new('RGB', (mm(TH - 16), mm(30)), (8, 8, 8)); sd = ImageDraw.Draw(strip)
    f = font('serifb', mm(3.2)); y = mm(4)
    for ln in FOOTER: sd.text(((strip.width - sd.textlength(ln, font=f)) / 2, y), ln, font=f, fill=WHITE); y += mm(4.4)
    strip = strip.rotate(-90, expand=True); c.paste(strip, (X[0] + mm(3), top))
    # spine panel: title running down
    sp = Image.new('RGBA', (mm(TH - 16), mm(26)), (0, 0, 0, 0)); spd = ImageDraw.Draw(sp)
    f = font('serifb', mm(11)); s = 'MIRE MARE'
    spd.text(((sp.width - spd.textlength(s, font=f)) / 2, mm(6)), s, font=f, fill=WHITE)
    sp = sp.rotate(-90, expand=True); c.paste(sp, (X[1] + mm(3), top), sp)
    # front panel: 48K line, logo, small painting, badge
    f = font('serifb', mm(5.2)); s = '48K SINCLAIR ZX SPECTRUM'
    d.text(((X[2] + X[3] - d.textlength(s, font=f)) / 2, top - mm(2)), s, font=f, fill=WHITE)
    pw, ph = mm(100), mm(84)
    pic = framed(painting(pw, ph, focus=.5), mm(5)); c.paste(pic, ((X[2] + X[3] - pw) // 2, top + mm(28)), pic)
    t = title_logo(mm(36)); c.paste(t, ((X[2] + X[3] - t.width) // 2, top + mm(6)), t)
    b = badge(mm(80)); c.paste(b, ((X[2] + X[3] - b.width) // 2, bot - b.height), b)
    # controls panel
    x0, x1 = X[3] + mm(7), X[4] - mm(6); y = top
    fh = font('serifb', mm(5)); fs = font('serifb', mm(3.6)); fb = font('serif', mm(3.3)); fk = font('serifb', mm(3.3))
    y = heading(d, x0 - mm(2), x1 + mm(2), y, 'CONTROLLING YOUR EXPLORER', font('serifb', mm(4.6)))
    for it in CONTROLS[1:]:
        if it[0] == 's': y += mm(1.5); d.text((x0, y), it[1], font=fs, fill=WHITE); y += mm(5.2)
        elif it[0] == 'p':
            for ln in wrap(d, it[1], fb, x1 - x0): d.text((x0, y), ln, font=fb, fill=WHITE); y += mm(4.1)
            y += mm(1)
        else:
            lab = it[1] + ' '; lw = d.textlength(lab, font=fk)
            lines = wrap(d, it[2], fb, x1 - x0 - lw)
            d.text((x0, y), lab, font=fk, fill=WHITE)
            for ln in lines: d.text((x0 + lw, y), ln, font=fb, fill=WHITE); y += mm(4.1)
            y += mm(.6)
    # loading panel
    x0, x1 = X[4] + mm(7), X[5] - mm(7); y = top
    y = heading(d, x0, x1, y, 'MIRE MARE', fh); y = heading(d, x0, x1, y - mm(2.5), 'LOADING INSTRUCTIONS', fh)
    fl = font('serifb', mm(3.3))
    for i, s in enumerate(LOADING):
        d.text((x0, y), f'{i + 1}.', font=fl, fill=WHITE)
        for ln in wrap(d, s, fl, x1 - x0 - mm(6)): d.text((x0 + mm(6), y), ln, font=fl, fill=WHITE); y += mm(4.1)
        y += mm(1.4)
    y += mm(2); y = heading(d, x0, x1, y, 'GUARANTEE', font('serifb', mm(4.2)))
    y = centred_block(d, x0, x1, y - mm(1), [GUARANTEE], font('serif', mm(2.5)), lead=1.15)
    y += mm(1); y = heading(d, x0, x1, y, 'COPYRIGHT NOTICE', font('serifb', mm(4.2)))
    centred_block(d, x0, x1, y - mm(1), [COPYRIGHT], font('serif', mm(2.5)), lead=1.15)
    folds(d, o, xs[1:-1], H)
    return c
def inner():
    c, d, o = canvas(); H = c.height
    xs = [0, 137.3, 274.6, 412]; X = [o + mm(v) for v in xs]
    top, bot = o + mm(8), o + mm(TH - 7)
    fh = font('serifb', mm(5.4))
    # panel 1: THE DREAMING + THE WARNING
    x0, x1 = X[0] + mm(9), X[1] - mm(9)
    y = heading(d, x0, x1, top, PROSE[0][0], fh)
    f = fit_size('serifb', x0, x1, PROSE[0][1], mm(70), mm(4.3), d)
    y = centred_block(d, x0, x1, y, PROSE[0][1], f)
    y = max(y, top + mm(84)); y = heading(d, x0, x1, y, RIDDLE_HEAD, fh)
    fr = font('serifb', mm(3.55))
    for ln in RIDDLE:
        while d.textlength(ln, font=fr) > x1 - x0 + mm(4): fr = font('serifb', fr.size - 1)
    for ln in RIDDLE: d.text(((x0 + x1 - d.textlength(ln, font=fr)) / 2, y), ln, font=fr, fill=WHITE); y += mm(4.55)
    # panel 2: THE WAKING + THE FEN
    x0, x1 = X[1] + mm(9), X[2] - mm(9)
    y = heading(d, x0, x1, top, PROSE[1][0], fh)
    f = fit_size('serifb', x0, x1, PROSE[1][1] + PROSE[2][1], mm(128), mm(4.6), d)
    y = centred_block(d, x0, x1, y, PROSE[1][1], f)
    y += mm(4); y = heading(d, x0, x1, y, PROSE[2][0], fh)
    y = centred_block(d, x0, x1, y, PROSE[2][1], f)
    fsm = font('serif', mm(2.3))
    centred_block(d, x0, x1, bot - mm(9), ["Due to the enormous size and complexity of this MIRE MARE adventure, the night may fall sooner than you expect. "
                  "Should a fault ever be found, please contact us, so that it may be corrected in all future versions."], fsm, lead=1.1)
    # panel 3: FEATURES
    x0, x1 = X[2] + mm(9), X[3] - mm(9)
    y = heading(d, x0, x1, top, 'FEATURES', fh)
    ff = font('serif', mm(3.45)); cx = [x0 + mm(6), (x0 + x1) / 2 + mm(1)]
    for k, col in enumerate(FEATURES):
        yy = y
        for it in col: d.text((cx[k], yy), it, font=ff, fill=WHITE); yy += mm(4.75)
    y = yy + mm(5)
    fb = font('serifb', mm(3.4))
    for i, ln in enumerate(FOOTER):
        g = fb if i else font('serif', mm(3.4)); d.text(((x0 + x1 - d.textlength(ln, font=g)) / 2, y), ln, font=g, fill=WHITE); y += mm(4.6)
    folds(d, o, xs[1:-1], H)
    return c
if __name__ == '__main__':
    a, b = outer(), inner()
    a.save('out/03_inlay_outer.png', dpi=(300, 300)); b.save('out/03_inlay_inner.png', dpi=(300, 300))
    a.resize((a.width // 4, a.height // 4)).save('work/prev_inlay_outer.png'); b.resize((b.width // 4, b.height // 4)).save('work/prev_inlay_inner.png')
