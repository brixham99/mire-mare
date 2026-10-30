#!/usr/bin/env python3
"""progression.py - can the whole quest be done without cheats?
Tile-level flood fill over all 160 generated screens (build/rooms_gen.json via
worldcache), applying the same day/night/item tile swaps as room_post.
Sabreman may wait for night or day anywhere he stands on dry land, so the
fill alternates day and night until nothing new is reached, collecting the
lantern, key and lever as they become reachable.  Reports what is reachable."""
import json, os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import worldcache
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = {}
for line in open(os.path.join(ROOT, 'data/tiles.asm')):
    if line.startswith('TILE_'): k, _, v = line.split(); T[k[5:]] = int(v)
FL = json.load(open(os.path.join(ROOT, 'build/tile_flags.json')))
W = worldcache.load(); WJ = json.load(open(os.path.join(ROOT, 'build/world.json')))
KIND = {1: 'light', 2: 'bit', 3: 'rein', 4: 'headstall', 5: 'buckle', 6: 'lantern', 7: 'key', 8: 'lever', 9: 'bud'}

def tile(r, x, y, night, has):
    t = W[r]['buf'][y * 16 + x]
    if night:
        if t == T['NIGHTLILY']: t = T['LILYPAD']
        elif t == T['SHALLOW']: t = T['BOG']
        elif t == T['CAUSEWAYSUNK']: t = T['CAUSEWAY'] if 'lever' in has else T['LILYPAD']
        elif t == T['SPIRITDOOR'] and 'lantern' in has: t = T['FLAGSTONE']
    elif t == T['CAUSEWAYSUNK'] and 'lever' in has: t = T['CAUSEWAY']
    if t == T['CRYPTDOOR'] and 'key' in has: t = T['FLAGSTONE']
    return t
def passable(r, x, y, night, has):
    f = FL[tile(r, x, y, night, has)]
    return not (f & 1) and not (f & 4)
def item_at(r):
    it = W[r]['item']
    if not it or it[0] == 255: return None
    return tuple(it)
def fill(seeds, night, has):
    seen = set(s for s in seeds if passable(*s, night, has)); q = deque(seen)
    while q:
        r, x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, nx, ny = r, x + dx, y + dy
            if nx < 0: rr, nx = r - 1, 15
            elif nx > 15: rr, nx = r + 1, 0
            elif ny < 1: rr, ny = r - 16, 10
            elif ny > 10: rr, ny = r + 16, 1
            if rr != r and (rr < 0 or rr >= 160 or (rr % 16) != (r % 16) + dx and dx): continue
            n = (rr, nx, ny)
            if n in seen: continue
            it = item_at(rr)
            if it and (nx, ny) == it:                       # items can be taken from a pool edge
                seen.add(n); continue
            if passable(rr, nx, ny, night, has): seen.add(n); q.append(n)
    return seen
def wade(r, it, reach, has):
    """a pool item counts if dry ground is within 3 non-solid tiles (a short bog wade)"""
    q = deque([(it[0], it[1], 0)]); seen = {it}
    while q:
        x, y, d = q.popleft()
        if (r, x, y) in reach: return True
        if d == 3: continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < 16 and 1 <= n[1] < 11 and n not in seen and not FL[tile(r, *n, 0, has)] & 1:
                seen.add(n); q.append((n[0], n[1], d + 1))
    return False
def run(verbose=True):
    has = set(); start = {(99, 8, 5)}
    reach = set(start); prev = -1
    while len(reach) != prev:
        prev = len(reach)
        for night in (0, 1):
            dry = {c for c in reach if passable(*c, night, has)}
            reach |= fill(dry, night, has)
            for r in range(160):
                it = item_at(r)
                if it and (r, *it) in reach:
                    k = KIND.get(WJ[str(r)]['item'])
                    if k in ('lantern', 'key', 'lever'): has.add(k)
    got = {}
    for r in range(160):
        it = item_at(r)
        if it:
            k = KIND.get(WJ[str(r)]['item'], '?')
            got.setdefault(k, [0, 0]); got[k][1] += 1
            if (r, *it) in reach or wade(r, it, reach, has): got[k][0] += 1
    rooms = {c[0] for c in reach}
    if verbose:
        print('rooms reachable: %d/160, tools: %s' % (len(rooms), sorted(has)))
        for k, (a, n) in sorted(got.items()): print('  %-10s %d/%d' % (k, a, n))
    return rooms, got, has
if __name__ == '__main__':
    rooms, got, has = run()
    ok = len(rooms) == 160 and all(a == n for a, n in got.values())
    print('COMPLETABLE' if ok else 'NOT COMPLETABLE'); sys.exit(0 if ok else 1)
