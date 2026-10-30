#!/usr/bin/env python3
"""Align the Fuse movie frames (build/fmf) with a headless replay of the same
DEMO build: finds the frame offset, checks that every room change of the
headless run appears in Fuse at the same relative frame, and saves Fuse
screenshots of the key moments into shots/fuse_v_*.png plus a GIF."""
import glob, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from headless import Game, ROOT
fr = sorted(glob.glob(os.path.join(ROOT, 'build/fmf/f-*.png')))
def fuse_bin(i):
    a = np.asarray(Image.open(fr[i]).convert('RGB'))[24:216, 32:288].astype(int)
    return (a[..., 2] > 100) * 1 + (a[..., 0] > 100) * 2 + (a[..., 1] > 100) * 4
def head_bin(g):
    a = np.zeros((192, 256), int)
    for y in range(192):
        base = 0x4000 | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
        for c in range(32):
            byte = g.mem[base + c]; at = g.mem[0x5800 + (y >> 3) * 32 + c]
            ink, paper = at & 7, (at >> 3) & 7
            for b in range(8):
                col = ink if byte & (0x80 >> b) else paper
                a[y, c * 8 + b] = col
    return a
# headless replay; snapshot binaries at chosen frames
g = Game('miremare_demo')
marks = []; last = None; snaps = {}
for f in range(3600):
    g.frame()
    r = g.b('cur_room')
    if r != last:
        marks.append((f, r)); last = r
    if r != 0 and f % 1 == 0 and len(snaps) < 1 and f > 150:
        snaps[f] = head_bin(g)
f0, ref = next(iter(snaps.items()))
best = None
for i in range(len(fr)):
    d = (fuse_bin(i) != ref).mean()
    if best is None or d < best[0]: best = (d, i)
off = best[1] - f0
print('reference headless frame %d matches fuse frame %d (diff %.4f): offset %d' % (f0, best[1], best[0], off))
# verify: for checkpoints in the headless run, find the identical screen in Fuse
ev = json.load(open(os.path.join(ROOT, 'build/bot_events.json')))
g = Game('miremare_demo')
cps = sorted({f + 40 for f, _ in marks[1:]} | set(range(200, 3500, 150)))
checks = []; cursor = 0
for f in range(max(cps) + 1):
    g.frame()
    if f in cps:
        h = head_bin(g); lo = max(cursor, f + off - 300); hi = min(len(fr), f + off + 300)
        bd = min(((fuse_bin(i) != h).mean(), i) for i in range(lo, hi))
        checks.append(dict(head=f, fuse=bd[1], room=g.b('cur_room'), night=g.b('night'), diff=round(float(bd[0]), 5)))
        cursor = bd[1]
        print(checks[-1])
json.dump(dict(offset=off, marks=marks, checks=checks), open(os.path.join(ROOT, 'build/fuse_align.json'), 'w'), indent=1)
bad = [c for c in checks if c['diff'] > 0.002]
print('%d/%d checkpoints identical in Fuse' % (len(checks) - len(bad), len(checks)))

# ---- export Fuse screenshots of the key moments + a GIF
g = Game('miremare_demo')
want = {60: 'fen_start'}; last = None; seen_mare = won = None; msgs = 0; prev_msg = 0
names = {83: 'fen_walk', 144: 'fen_bit', 20: 'wood_lantern', 0: 'wood_rein', 63: 'hags_key',
         159: 'hags_buckle', 24: 'abbey_crypt', 10: 'abbey_headstall', 86: 'mere_night', 104: 'isle'}
for f in range(3600):
    g.frame()
    r = g.b('cur_room')
    if r != last and r in names and f > 5: want[f + 30] = names[r]
    last = r
    if g.b('mare_here') and seen_mare is None and g.b('night'):
        seen_mare = f; want[f + 25] = 'mare_night'; want[f + 90] = 'mare_night2'
    if g.b('game_won') and won is None:
        won = f; want[f] = 'bridling'
    if f in want: want[f] = (want[f], head_bin(g)) if not isinstance(want[f], tuple) else want[f]
for name, v in [('wood_rein', None)]: pass
c = json.load(open(os.path.join(ROOT, 'build/fuse_align.json')))['checks']
def fuse_guess(f):
    best = min(c, key=lambda k: abs(k['head'] - f)); return f + best['fuse'] - best['head']
os.makedirs(os.path.join(ROOT, 'shots'), exist_ok=True)
for f, (name, h) in sorted(want.items()):
    gs = fuse_guess(f)
    d, i = min(((fuse_bin(i) != h).mean(), i) for i in range(max(0, gs - 120), min(len(fr), gs + 120)))
    Image.open(fr[i]).resize((640, 480), Image.NEAREST).save(os.path.join(ROOT, 'shots/fuse_v_%s.png' % name))
    print('fuse frame %5d  %-16s diff %.5f' % (i, name, d))
# ending and rating: fuse frames are found by text screens after the win
wf = fuse_guess(won)
def is_rating(i):
    a = np.asarray(Image.open(fr[i]).convert('RGB'))[24:216, 32:288]
    return a[0:8, 200:256].max() > 0 and a[150:192].max() == 0
rt = next((i for i in range(wf + 100, len(fr)) if is_rating(i)), len(fr) - 1)
for name, k in (('ending', wf + 250), ('rating', rt + 60)):
    Image.open(fr[min(len(fr) - 1, k)]).resize((640, 480), Image.NEAREST).save(os.path.join(ROOT, 'shots/fuse_v_%s.png' % name))
# GIF: whole run at 12.5 fps, 1x size
gif = [Image.open(fr[i]).convert('P', palette=Image.ADAPTIVE, colors=16) for i in range(300, min(len(fr), rt + 150), 4)]
gif[0].save(os.path.join(ROOT, 'shots/fuse_demo_run.gif'), save_all=True, append_images=gif[1:], duration=80, loop=0, optimize=True)
print('gif frames', len(gif))
