#!/usr/bin/env python3
"""validate_world.py - run the Z80 room generator (the real code, in the
headless core) for all 160 screens, check every room with a BFS over its
tiles, search generator seeds for rooms that fail, and save the seeds to
art/seeds.json.  Also renders build/map_preview.png.

Checks per room (tile level; Sabreman's 12x6 feet fit inside one tile):
  open : with night lilies, sunk causeway, spirit and crypt doors passable
         and deep bog blocked, every exit and the item are reachable
         (an item in a pool may be reached through bog)
  entry: every exit's entry cells are walkable
  day  : on land, exits whose gaps are plain ground are connected by day
  spawn: creature spawn points stand on walkable ground
  start: the start position is clear and connected
Usage: validate_world.py [--search] [--preview]"""
import json, os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(__file__))
from headless import Game, ROOT, lib

T = {}
for line in open(os.path.join(ROOT, 'data/tiles.asm')):
    if line.startswith('TILE_'):
        k, _, v = line.split(); T[k[5:]] = int(v)
WORLD = json.load(open(os.path.join(ROOT, 'build/world.json')))

class Gen:
    def __init__(self):
        self.g = Game(entry='dbg_gen')
        S = self.g.S
        self.flags = self.g.block('tile_flags', len(T))
    def run(self, room, seed=None):
        g = self.g
        if seed is not None:
            g.mem[g.S['world_tab'] + room * 7 + 1] = seed
        g.poke('dbg_room', room)
        lib.z_setpc(g.S['dbg_gen'])
        for _ in range(40):
            g.frame()
            if g.pc() in (g.S['dbg_end'], g.S['dbg_end'] + 1): break
        else:
            raise RuntimeError('generator did not finish for room %d' % room)
        buf = list(g.block('roombuf', 176))
        sp = list(g.block('gen_sp', 8))
        return dict(buf=buf, item=(g.b('item_tx'), g.b('item_ty')), sp=sp,
                    pool=(g.b('pool_cx'), g.b('pool_cy')))

def passable(t, flags, mode):
    if mode == 'open':
        if t in (T['NIGHTLILY'], T['CAUSEWAYSUNK'], T['SPIRITDOOR'], T['CRYPTDOOR']): return True
        if t == T['BOG']: return False
    if mode == 'day' and t == T['BOG']: return False
    return not (flags[t] & 1)

def exits_cells(rec):
    ex = rec['exits']
    out = {}
    if ex & 1: out['N'] = [(c, 1) for c in range(6, 10)]
    if ex & 4: out['S'] = [(c, 10) for c in range(6, 10)]
    if ex & 8: out['W'] = [(0, r) for r in range(4, 7)]
    if ex & 2: out['E'] = [(15, r) for r in range(4, 7)]
    return out

def bfs(buf, flags, mode, start, allow_bog=False):
    seen = set(); q = deque()
    for s in start:
        x, y = s
        t = buf[y * 16 + x]
        if passable(t, flags, mode) or (allow_bog and t == T['BOG']):
            seen.add(s); q.append(s)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < 16 and 1 <= ny < 11) or (nx, ny) in seen: continue
            t = buf[ny * 16 + nx]
            if passable(t, flags, mode) or (allow_bog and t == T['BOG']):
                seen.add((nx, ny)); q.append((nx, ny))
    return seen

def check(room, res, flags):
    rec = WORLD[str(room)]
    buf = res['buf']; errs = []
    ex = exits_cells(rec)
    # gap cells themselves (row 0 for N) and entry cells
    for d, cells in ex.items():
        test = cells[:]
        if d == 'N': test += [(c, 0) for c in range(6, 10)]
        if d == 'E': test += [(14, r) for r in range(4, 7)]
        if d == 'W': test += [(1, r) for r in range(4, 7)]
        bad = [c for c in test if not passable(buf[c[1] * 16 + c[0]], flags, 'open')]
        if bad: errs.append('exit %s blocked at %s' % (d, bad[:2]))
    if errs: return errs
    allcells = [c for cells in ex.values() for c in cells]
    if allcells:
        reach = bfs(buf, flags, 'open', allcells[:1])
        for d, cells in ex.items():
            if not any(c in reach for c in cells): errs.append('exit %s unreachable (open)' % d)
        ix, iy = res['item']
        if ix != 255:
            reach_b = bfs(buf, flags, 'open', allcells[:1], allow_bog=bool(rec['inpool']))
            if (ix, iy) not in reach_b: errs.append('item unreachable')
    # day connectivity of plain land exits
    if rec['region'] not in (4, 5):
        plain = {d: c for d, c in ex.items()
                 if all(passable(buf[y * 16 + x], flags, 'day') for x, y in c)}
        ds = list(plain)
        if len(ds) > 1:
            reach = bfs(buf, flags, 'day', plain[ds[0]])
            for d in ds[1:]:
                if not any(c in reach for c in plain[d]): errs.append('exit %s cut off by day' % d)
    sp = res['sp']
    for i in range(4):
        x, y = sp[2 * i], sp[2 * i + 1]
        if x == 255: continue
        cx, cy = (x + 8) // 16, (y + 8) // 16
        if not (0 <= cx < 16 and 0 <= cy < 11): errs.append('spawn %d off-room' % i); continue
        t = buf[cy * 16 + cx]
        if flags[t] & 1 and i < 3 and rec['region'] != 4: errs.append('spawn %d in scenery' % i)
    return errs

def start_ok(gen, res, flags):
    g = gen.g
    sx, sy = g.S['START_X'], g.S['START_Y']
    buf = res['buf']
    cells = {((sx + 6 + dx) // 16, (sy + 18 + dy) // 16) for dx in (0, 11) for dy in (0, 5)}
    for x, y in cells:
        if flags[buf[y * 16 + x]] & 5: return False
    return True

def main():
    search = '--search' in sys.argv
    gen = Gen(); flags = gen.flags
    seeds_path = os.path.join(ROOT, 'art/seeds.json')
    seeds = json.load(open(seeds_path)) if os.path.exists(seeds_path) else {}
    bad = {}; results = {}
    START = gen.g.S['START_ROOM']
    for room in range(160):
        res = gen.run(room)
        errs = check(room, res, flags)
        if room == START and not start_ok(gen, res, flags): errs.append('start blocked')
        if errs and search:
            for seed in range(2, 256):
                r2 = gen.run(room, seed)
                e2 = check(room, r2, flags)
                if room == START and not start_ok(gen, r2, flags): e2.append('start blocked')
                if not e2:
                    seeds[str(room)] = seed; res, errs = r2, []
                    break
        results[room] = res
        if errs: bad[room] = errs
    if search:
        json.dump(seeds, open(seeds_path, 'w'), indent=0, sort_keys=True)
    for r, e in sorted(bad.items()):
        print('room %3d %s: %s' % (r, WORLD[str(r)]['region'], '; '.join(e)))
    print('%d/160 rooms valid' % (160 - len(bad)))
    if '--preview' in sys.argv: preview(gen, results)
    return len(bad)

def preview(gen, results):
    from PIL import Image
    g = gen.g
    gfx = g.block('tile_gfx', 36 * len(T))
    pal = []
    for br in (0xD7, 0xFF):
        for c in range(8): pal.append(((c & 2) and br or 0, (c & 4) and br or 0, (c & 1) and br or 0))
    tiles = []
    for t in range(len(T)):
        im = Image.new('RGB', (16, 16)); p = im.load(); d = gfx[t * 36:(t + 1) * 36]
        for y in range(16):
            for bx in range(2):
                byte = d[y * 2 + bx]; at = d[32 + (y // 8) * 2 + bx]
                br = 8 if at & 64 else 0
                for b in range(8):
                    p[bx * 8 + b, y] = pal[(at & 7) + br] if byte & (0x80 >> b) else pal[((at >> 3) & 7) + br]
        tiles.append(im)
    W = 256 + 4; H = 176 + 4
    img = Image.new('RGB', (16 * W, 10 * H), (40, 40, 40))
    for room, res in results.items():
        ox, oy = (room % 16) * W, (room // 16) * H
        for i, t in enumerate(res['buf']):
            img.paste(tiles[t], (ox + (i % 16) * 16, oy + (i // 16) * 16))
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    img.save(os.path.join(ROOT, 'build/map_preview.png'))
    print('wrote build/map_preview.png', img.size)

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
