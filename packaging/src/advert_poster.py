"""Magazine advert (A4 full page, 210x297 + 3 mm bleed) and poster (A3, 297x420 + 3 mm bleed), 300 dpi."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from front import matte_black, painting, framed
def advert():
    W, H = mm(216), mm(303); o = mm(3); c = matte_black(W, H, 7); d = ImageDraw.Draw(c)
    pw, ph = mm(186), mm(214)
    pic = framed(painting(pw, ph, focus=.45), mm(8)); c.paste(pic, ((W - pw) // 2, o + mm(40)), pic)
    t = title_logo(mm(62)); c.paste(t, ((W - t.width) // 2, o + mm(6)), t)
    b = badge(mm(120)); c.paste(b, ((W - b.width) // 2, o + mm(232)), b)
    f = font('serifb', mm(6)); s = '48K SINCLAIR ZX SPECTRUM   \u00a39.95'
    y = o + mm(232) + b.height + mm(4)
    d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=(245, 245, 240))
    fs = font('serif', mm(3.2))
    centred_block(d, mm(20), W - mm(20), y + mm(9), ['"MIRE MARE" recommended retail price \u00a39.95 inc. VAT. Available from all good software retailers, or direct from',
        'ULTIMATE PLAY THE GAME, The Green, Ashby de la Zouch, Leicestershire. (P&P included)'], fs, gap=.1)
    return c
def poster():
    W, H = mm(303), mm(426); o = mm(3)
    c = painting(W, H, focus=.5).convert('RGB')
    # darken the top and bottom so the lettering and badge sit on near-black, like the box
    sh = vgrad(1, H, [(0, (0, 0, 0)), (.16, (255, 255, 255)), (.84, (255, 255, 255)), (1, (0, 0, 0))]).convert('L').resize((W, H))
    c = Image.composite(c, Image.new('RGB', (W, H), 'black'), sh)
    t = title_logo(mm(110)); c.paste(t, ((W - t.width) // 2, o + mm(10)), t)
    b = badge(mm(150)); c.paste(b, ((W - b.width) // 2, H - o - mm(12) - b.height), b)
    return c
if __name__ == '__main__':
    a = advert(); a.save('out/05_advert_A4.png', dpi=(300, 300)); a.resize((a.width // 5, a.height // 5)).save('work/prev_ad1.png')
    p = poster(); p.save('out/05_poster_A3.png', dpi=(300, 300)); p.resize((p.width // 7, p.height // 7)).save('work/prev_po1.png')
