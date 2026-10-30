"""Shared drawing helpers for the Mire Mare packaging (Pillow only)."""
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
G = '/usr/share/fonts/truetype/sand-box/google/'
DPI = 300
def mm(x): return int(round(x / 25.4 * DPI))
def font(name, size):
    p = {'title': 'Metal Mania/MetalMania-Regular.ttf', 'badge': 'Russo One/RussoOne-Regular.ttf',
         'serif': 'Tinos/Tinos-Regular.ttf', 'serifb': 'Tinos/Tinos-Bold.ttf',
         'serifi': 'Tinos/Tinos-Italic.ttf', 'sans': 'Roboto Condensed/RobotoCondensed-VariableFont_wght.ttf'}[name]
    return ImageFont.truetype(G + p, size)

def vgrad(w, h, stops):
    """vertical gradient, stops = [(t, (r,g,b)), ...]"""
    g = Image.new('RGB', (1, h)); px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / max(1e-6, t1 - t0)
                px[0, y] = tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3)); break
    return g.resize((w, h))

def warp(mask, amp, period, seed=3):
    """organic hand-lettered wobble: displace columns and rows by smooth sines"""
    w, h = mask.size; out = Image.new('L', (w, h)); src = mask.load(); dst = out.load()
    rnd = random.Random(seed); ph = [rnd.random() * 6.28 for _ in range(4)]
    import numpy as np
    a = np.array(mask); ys, xs = np.mgrid[0:h, 0:w]
    dx = amp * np.sin(ys / period + ph[0]) + amp * .5 * np.sin(ys / (period * .37) + ph[1])
    dy = amp * np.sin(xs / (period * 1.3) + ph[2]) + amp * .4 * np.sin(xs / (period * .29) + ph[3])
    sx = np.clip((xs + dx).astype(int), 0, w - 1); sy = np.clip((ys + dy).astype(int), 0, h - 1)
    return Image.fromarray(a[sy, sx])

def dilate(mask, r):
    """fast round dilation: distance via blur+threshold (good enough for outlines)"""
    if r <= 0: return mask
    import numpy as np
    from scipy import ndimage
    a = np.array(mask) > 127
    dist = ndimage.distance_transform_edt(~a)
    return Image.fromarray(((dist <= r) * 255).astype('uint8'))

def title_logo(height, two_line=True, seed=7, mono=None):
    """Hand-lettered MIRE MARE logotype: swash capitals, moonlit violet fill,
    white keyline, black outline and drips. Returns RGBA."""
    S = 2 * height  # draw big, then scale
    f = font('title', int(S * .52))
    W = int(S * (1.6 if two_line else 3.2)); H = S
    m = Image.new('L', (W, H)); d = ImageDraw.Draw(m)
    if two_line:
        d.text((int(W * .04), int(S * .02)), 'Mire', font=f, fill=255)
        d.text((int(W * .30), int(S * .44)), 'Mare', font=f, fill=255)
    else:
        f = font('title', int(S * .7)); d.text((10, 10), 'Mire Mare', font=f, fill=255)
    m = m.crop(m.getbbox()); pad = int(S * .12)
    mm_ = Image.new('L', (m.width + 2 * pad, m.height + 2 * pad)); mm_.paste(m, (pad, pad)); m = mm_
    m = warp(m, S * .008, S * .05, seed)
    # drips of mire hanging from the letters
    rnd = random.Random(seed); d = ImageDraw.Draw(m); import numpy as np
    a = np.array(m)
    for _ in range(14):
        x = rnd.randrange(pad, m.width - pad)
        col = np.nonzero(a[:, x] > 128)[0]
        if len(col) == 0: continue
        y = col.max(); L = rnd.randint(int(S * .03), int(S * .11)); r = rnd.randint(int(S * .008), int(S * .016))
        d.rectangle((x - r // 2, y - 2, x + r // 2, y + L), fill=255); d.ellipse((x - r, y + L - r, x + r, y + L + r), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(S * .004)).point(lambda v: 255 if v > 120 else 0)
    k1 = int(S * .018); k2 = int(S * .045)
    inner = m
    white = dilate(m, k1)
    black = dilate(m, k2)
    w, h = m.size
    if mono:  # outline lettering for one-colour print: white keyline, ground showing through
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); out.paste(mono + (255,), (0, 0), white)
        out.paste((0, 0, 0, 0), (0, 0), dilate(inner, 0) if False else inner.filter(ImageFilter.MinFilter(5)))
        out = out.crop(out.getbbox()); r = height / out.height
        return out.resize((int(out.width * r), height), Image.LANCZOS)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 0), black)
    out.paste((255, 255, 255, 255), (0, 0), white)
    fill = vgrad(w, h, [(0, (255, 250, 220)), (.25, (240, 150, 255)), (.55, (170, 40, 220)), (.8, (70, 10, 120)), (1, (30, 90, 60))])
    # airbrushed highlight band
    hl = Image.new('L', (w, h)); ImageDraw.Draw(hl).rectangle((0, 0, w, int(h * .22)), fill=110)
    hl = hl.filter(ImageFilter.GaussianBlur(S * .03))
    fill = Image.composite(Image.new('RGB', (w, h), (255, 255, 255)), fill, hl)
    out.paste(fill, (0, 0), inner)
    # inner shading: darken lower edge of each stroke
    sh = ImageChops.subtract(inner, inner.transform(inner.size, Image.AFFINE, (1, 0, 0, 0, 1, -int(S * .012))))
    out.paste((40, 0, 70, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(2)))
    out = out.crop(out.getbbox())
    r = height / out.height
    return out.resize((int(out.width * r), height), Image.LANCZOS)

def badge(width, frame=True):
    """ULTIMATE / PLAY THE GAME badge (chrome-rainbow lettering in a ruled black box)."""
    S = width * 3
    fu = font('badge', int(S * .2)); fp = font('badge', int(S * .085))
    W = S; H = int(S * .40)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(out)
    if frame:
        lw = max(3, int(S * .012))
        d.rounded_rectangle((lw, lw, W - lw - 1, H - lw - 1), radius=int(S * .03), outline=(235, 235, 235), width=lw)
    # ULTIMATE
    m = Image.new('L', (W, H)); dm = ImageDraw.Draw(m)
    bb = dm.textbbox((0, 0), 'ULTIMATE', font=fu); tw = bb[2] - bb[0]
    sx = W * .86 / tw
    t = Image.new('L', (bb[2] + 4, bb[3] + 4)); ImageDraw.Draw(t).text((0, 0), 'ULTIMATE', font=fu, fill=255)
    t = t.crop(t.getbbox()); t = t.resize((int(t.width * sx * .99), int(t.height * 1.25)))
    ux = (W - t.width) // 2; uy = int(H * .1)
    m.paste(t, (ux, uy))
    th = t.height
    chrome = vgrad(W, H, [(0, (120, 255, 120)), (uy / H, (120, 255, 120)), ((uy + th * .46) / H, (230, 255, 160)),
                          ((uy + th * .5) / H, (40, 60, 150)), ((uy + th * .62) / H, (60, 200, 255)), ((uy + th) / H, (220, 120, 255)), (1, (220, 120, 255))])
    # horizontal chrome scanlines
    cd = ImageDraw.Draw(chrome)
    for y in range(uy, uy + th, max(2, int(th / 14))):
        cd.line((0, y, W, y), fill=(255, 255, 255) if y < uy + th * .45 else (20, 30, 90), width=1)
    ol = dilate(m, max(2, int(S * .006)))
    out.paste((255, 255, 255), (0, 0), ol)
    out.paste(chrome, (0, 0), m)
    # PLAY THE GAME
    p = Image.new('L', (W, H)); dp = ImageDraw.Draw(p)
    bb = dp.textbbox((0, 0), 'PLAY THE GAME', font=fp)
    pt = Image.new('L', (bb[2] + 4, bb[3] + 4)); ImageDraw.Draw(pt).text((0, 0), 'PLAY THE GAME', font=fp, fill=255)
    pt = pt.crop(pt.getbbox()); pt = pt.resize((int(W * .74), pt.height))
    py = uy + th + int(H * .07)
    p.paste(pt, ((W - pt.width) // 2, py))
    pc = vgrad(W, H, [(0, (90, 230, 255)), (py / H, (160, 255, 255)), ((py + pt.height) / H, (40, 150, 230)), (1, (40, 150, 230))])
    out.paste((255, 255, 255), (0, 0), dilate(p, 2))
    out.paste(pc, (0, 0), p)
    out = out.resize((width, int(H * width / W)), Image.LANCZOS)
    return out

# ---------------- text layout ----------------
def wrap(d, text, f, width):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def centred_block(d, x0, x1, y, paras, f, fill=(240, 240, 240), lead=1.18, gap=.55, draw=True, align='centre'):
    """draw wrapped paragraphs centred between x0..x1; returns new y"""
    lh = f.size * lead
    for p in paras:
        for ln in wrap(d, p, f, x1 - x0):
            if draw:
                if align == 'centre': d.text(((x0 + x1 - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=fill)
                else: d.text((x0, y), ln, font=f, fill=fill)
            y += lh
        y += f.size * gap
    return y

def heading(d, x0, x1, y, text, f, fill=(255, 255, 255)):
    d.text(((x0 + x1 - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)
    return y + f.size * 1.5

def fit_size(fn, x0, x1, paras, maxh, start, d):
    s = start
    while s > 10:
        f = font(fn, s)
        if centred_block(d, x0, x1, 0, paras, f, draw=False) <= maxh: return f
        s -= 1
    return font(fn, s)
