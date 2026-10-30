#!/usr/bin/env python3
"""world.py - designs the 160-screen world of Mire Mare (16 x 10) and writes
data/world.asm: one 7-byte record per screen (see engine/roomgen.asm), plus
build/world.json for the validator, the map preview and the test bot.

Layout is fixed by hand (regions, gates, quest items); connections inside a
region are a seeded random spanning tree plus a few loops.  Room seeds are
chosen afterwards by tools/validate_world.py, which runs the real Z80 room
generator and checks every screen, and stores them in art/seeds.json."""
import json, os, random

W, H = 16, 10
GRID = """
WWWWWWaaaaaaPPPP
WWWWWWaaAaaaPPPP
WWWWWaaaaaaaPPPP
WWWWWaaaaaaaPPPP
SSSSSmmmmmmPPPPP
SSSSmmmIImmmPPPP
SSSSmmmIImmmPPPP
SSSSSmmmmmmPPPPP
SSSSSSSmmSSPPPPP
SSSSSSSSSSSPPPPP
""".split()
REG = {'S': 0, 'W': 1, 'a': 2, 'A': 2, 'P': 3, 'm': 4, 'I': 5}
NAMES = ['Sedge Fen', 'Gloaming Wood', 'Sunken Abbey', 'Peat Hags', 'The Mere', "Mare's Isle"]
N, E, S_, Wd = 1, 2, 4, 8
DIRS = {N: (0, -1), E: (1, 0), S_: (0, 1), Wd: (-1, 0)}
OPP = {N: S_, S_: N, E: Wd, Wd: E}
SANCTUM = {(9, 0), (10, 0), (11, 0)}
CRYPT = (8, 1)
START = (3, 6)
ENEMY = dict(wisp=0, toad=1, adder=2, heron=3, leech=4, boggart=5, monk=6, bogbody=7, ox=8, hag=9)
ITEM = dict(light=1, bit=2, rein=3, headstall=4, buckle=5, lantern=6, key=7, lever=8, bud=9)
QUEST = {(0, 9): 'bit', (0, 0): 'rein', (10, 0): 'headstall', (15, 9): 'buckle',
         (4, 1): 'lantern', (15, 3): 'key', CRYPT: 'lever'}

def reg(x, y): return REG[GRID[y][x]]
def group(x, y):
    if (x, y) in SANCTUM: return 'sanctum'
    if (x, y) == CRYPT: return 'crypt'
    return GRID[y][x].replace('A', 'a')

def build(rng_seed=1985):
    rng = random.Random(rng_seed)
    rooms = {(x, y): dict(x=x, y=y, region=reg(x, y), exits=0, lily=0, door=0, crypt=0,
                          causeway=0, item=0, inpool=0, pool=0, clumps=0, en=[], night=0)
             for y in range(H) for x in range(W)}
    def link(a, b, kind='open'):
        (ax, ay), (bx, by) = a, b
        d = {(1, 0): E, (-1, 0): Wd, (0, 1): S_, (0, -1): N}[(bx - ax, by - ay)]
        ra, rb = rooms[a], rooms[b]
        ra['exits'] |= d; rb['exits'] |= OPP[d]
        if kind == 'lily':
            if ra['region'] != 4: ra['lily'] |= d
            if rb['region'] != 4: rb['lily'] |= OPP[d]
        elif kind in ('door', 'crypt'):
            ra['door'] |= d; rb['door'] |= OPP[d]
            if kind == 'crypt': ra['crypt'] = rb['crypt'] = 1
    # spanning tree + loops inside each group
    groups = {}
    for (x, y) in rooms: groups.setdefault(group(x, y), []).append((x, y))
    for gname, cells in sorted(groups.items()):
        cs = set(cells)
        if gname in ('m', 'I'):
            for (x, y) in cells:
                for dx, dy in ((1, 0), (0, 1)):
                    if (x + dx, y + dy) in cs: link((x, y), (x + dx, y + dy), 'lily' if gname == 'm' else 'open')
            continue
        start = sorted(cells)[0]; seen = {start}; stack = [start]
        while stack:
            c = stack[-1]
            nb = [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            nb = [n for n in nb if n in cs and n not in seen]
            if not nb: stack.pop(); continue
            n = rng.choice(nb); link(c, n); seen.add(n); stack.append(n)
        for (x, y) in cells:
            for dx, dy in ((1, 0), (0, 1)):
                n = (x + dx, y + dy)
                if n in cs and rng.random() < 0.28:
                    link((x, y), n)
    # gates between regions
    for a, b in [((1, 4), (1, 3)), ((4, 4), (4, 3)),            # fen - wood
                 ((5, 1), (6, 1)), ((4, 3), (5, 3)),            # wood - abbey
                 ((11, 2), (12, 2)), ((11, 3), (12, 3)),        # abbey - hags
                 ((10, 9), (11, 9)), ((10, 8), (11, 8))]:       # fen - hags
        link(a, b)
    link((9, 1), (9, 0), 'door'); link((11, 1), (11, 0), 'door')    # spirit doors to the sanctum
    link((8, 2), CRYPT, 'crypt')
    # the Mere: lily paths from the shores, the causeway, the Isle
    for a, b in [((4, 4), (5, 4)), ((3, 5), (4, 5)), ((3, 6), (4, 6)), ((4, 7), (5, 7)),
                 ((6, 8), (7, 8)), ((9, 8), (8, 8)), ((8, 9), (8, 8)),
                 ((11, 4), (10, 4)), ((12, 5), (11, 5)), ((11, 7), (10, 7)),
                 ((5, 3), (5, 4)), ((9, 3), (9, 4)), ((10, 3), (10, 4)),
                 ((6, 5), (7, 5)), ((8, 4), (8, 5)), ((9, 6), (8, 6)), ((7, 7), (7, 6)),
                 ((7, 3), (7, 4)), ((7, 4), (7, 5))]:
        link(a, b, 'lily')
    for c in ((7, 3), (7, 4), (7, 5)): rooms[c]['causeway'] = 1
    # terrain
    POOLS = {0: [1, 2, 3, 4, 5, 0, 2, 3], 1: [0, 0, 1, 4, 0, 6, 2], 2: [0, 7, 4, 0, 6, 0],
             3: [2, 3, 3, 1, 6, 0, 2], 4: [0], 5: [0, 1]}
    CLUMPS = {0: (3, 6), 1: (6, 10), 2: (4, 8), 3: (3, 6), 4: (0, 0), 5: (2, 4)}
    for c, r in rooms.items():
        r['pool'] = rng.choice(POOLS[r['region']])
        r['clumps'] = rng.randint(*CLUMPS[r['region']])
    rooms[START]['pool'] = 1; rooms[START]['clumps'] = 3
    rooms[CRYPT]['pool'] = 0
    # items
    for c, k in QUEST.items(): rooms[c]['item'] = ITEM[k]
    land = [c for c, r in rooms.items() if r['region'] < 4 and c != START and not rooms[c]['item']
            and c not in SANCTUM]
    for rg in range(4):
        cand = [c for c in land if rooms[c]['region'] == rg and not rooms[c]['item']]
        for c in rng.sample(cand, 10):
            rooms[c]['item'] = ITEM['light']
            if rooms[c]['pool'] in (2, 3) and rng.random() < 0.6: rooms[c]['inpool'] = 1
    rest = [c for c in land if not rooms[c]['item']]
    for c in rng.sample(rest, 12): rooms[c]['item'] = ITEM['bud']
    # enemies
    POOL_EN = {0: ['toad', 'adder', 'heron', 'wisp', 'toad'], 1: ['boggart', 'wisp', 'toad', 'heron', 'boggart'],
               2: ['monk', 'leech', 'wisp', 'monk'], 3: ['ox', 'adder', 'leech', 'wisp', 'adder'],
               4: ['wisp', 'heron'], 5: []}
    for c, r in rooms.items():
        opts = POOL_EN[r['region']]
        if not opts: continue
        dist = abs(c[0] - START[0]) + abs(c[1] - START[1])
        n = 0 if dist == 0 else 1 if dist == 1 else rng.choice([1, 2, 2, 3] if r['region'] != 4 else [1, 1, 2])
        ens = []
        for _ in range(n):
            t = rng.choice(opts)
            if t == 'ox' and ('ox' in ens or n > 2): t = 'adder'
            ens.append(t)
        r['en'] = [ENEMY[t] for t in ens]
        if r['region'] in (0, 3) and r['pool'] in (1, 2, 3, 5) and rng.random() < 0.6:
            r['night'] = ENEMY['bogbody'] + 1
        if r['region'] == 4 and (c[0] * 7 + c[1] * 3) % 3 != 0:      # night hags (no rng: map unchanged)
            r['night'] = ENEMY['hag'] + 1
    return rooms

def record(r, seed):
    en = r['en'] + [None] * (3 - len(r['en']))
    e = [0 if t is None else t + 1 for t in en]
    return [r['exits'] | (r['region'] << 4) | (r['causeway'] << 7), seed,
            r['lily'] | (r['door'] << 4), r['item'] | (r['inpool'] << 4) | (r['crypt'] << 5),
            r['pool'] | (r['clumps'] << 4), e[0] | (e[1] << 4), e[2] | (r['night'] << 4)]

def write(rooms, seeds):
    out = ['; generated by tools/world.py - do not edit',
           'MAP_W EQU %d' % W, 'MAP_H EQU %d' % H, 'NUM_ROOMS EQU %d' % (W * H),
           'START_ROOM EQU %d' % (START[1] * W + START[0]),
           'START_X EQU 120', 'START_Y EQU 72',
           'ISLE_HOME EQU %d' % (6 * W + 8),
           'world_tab:']
    for y in range(H):
        for x in range(W):
            i = y * W + x
            out.append('        DEFB ' + ','.join('$%02X' % v for v in record(rooms[(x, y)], seeds.get(str(i), 1)))
                       + '   ; %d (%d,%d) %s' % (i, x, y, NAMES[rooms[(x, y)]['region']]))
    open('data/world.asm', 'w').write('\n'.join(out) + '\n')
    js = {str(y * W + x): dict(r, seed=seeds.get(str(y * W + x), 1)) for (x, y), r in rooms.items()}
    json.dump(js, open('build/world.json', 'w'))

if __name__ == '__main__':
    os.makedirs('build', exist_ok=True)
    seeds = json.load(open('art/seeds.json')) if os.path.exists('art/seeds.json') else {}
    rooms = build()
    write(rooms, seeds)
    cnt = {}
    for r in rooms.values(): cnt[NAMES[r['region']]] = cnt.get(NAMES[r['region']], 0) + 1
    print('world: %d screens' % len(rooms), cnt)
