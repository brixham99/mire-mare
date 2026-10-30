#!/usr/bin/env python3
"""walker.py - plays a whole game of Mire Mare in NORMAL mode: no god mode,
no warps, no clock or item cheats.  Live build, inputs only (every input is
logged, so the run replays tick-for-tick on the real ROM via ./build.sh demo).

Planner: a tile-level graph over all 160 screens (live room buffer for the
current screen, the generator cache + day/night/item swaps for the rest).
It walks to each quest item in turn (bit, lantern, rein, key, buckle, lever,
headstall), waits for night or day where a route needs it, then crosses to
Mare's Isle and bridles her.  A reflex layer fights: it faces and swings at
anything that comes near (creatures, clods, leeches, the Mare herself).

Writes build/walk_stream.asm, build/walk_log.json (deaths with room/cause)
and prints a summary.  Usage: walker.py [--stream] [--reflex-only] [--horizon N] [--tag name]"""
import json, os, sys, time
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot import Bot, R, L, D, U, F, ROOT
import progression as P

KIND = {2: 'bit', 3: 'rein', 4: 'headstall', 5: 'buckle', 6: 'lantern', 7: 'key', 8: 'lever'}
QUEST = {v: int(r) for r, w in P.WJ.items() for k, v in KIND.items() if w['item'] == k}
ISLE_HOME = 104
NAMES = ['Sedge Fen', 'Gloaming Wood', 'Sunken Abbey', 'Peat Hags', 'The Mere', "Mare's Isle"]

class Walker(Bot):
    def __init__(self):
        super().__init__()
        self.log = dict(deaths=[], rooms=[], waits=[], events=[])
        self.tick0 = 0
        self.ET = None
    # ------------------------------------------------------------- state
    def has(self):
        g = self.g; h = set()
        if g.b('has_lantern'): h.add('lantern')
        if g.b('has_key'): h.add('key')
        if g.b('causeway_up'): h.add('lever')
        return h
    def taken(self, r): return self.g.mem[self.g.S['room_flags'] + r] & 1
    def tile(self, r, x, y, night, has):
        if r == self.g.b('cur_room') and night == self.g.b('night'):
            return self.livebuf[y * 16 + x]
        t = P.tile(r, x, y, night, has)
        if self.flags[t] & 8 and self.taken(r): t = self.T['FLOOR']
        return t
    def ok(self, r, x, y, night, has, goal=None):
        if goal and (r, x, y) in goal: return True
        t = self.tile(r, x, y, night, has)
        f = self.flags[t]
        if f & 1 or f & 4: return False
        if t == self.T['BUD']: return False
        if t == self.T['SHALLOW'] and not night: return True
        return True
    def neighbours(self, n):
        r, x, y = n
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, nx, ny = r, x + dx, y + dy
            if nx < 0: rr, nx = r - 1, 15
            elif nx > 15: rr, nx = r + 1, 0
            elif ny < 1: rr, ny = r - 16, 10
            elif ny > 10: rr, ny = r + 16, 1
            if rr != r:
                if rr < 0 or rr >= 160: continue
                if dx and rr // 16 != r // 16: continue
            yield (rr, nx, ny)
    def bfs(self, start, goal, night, has, both=False, limit=60000, either=False):
        prev = {start: None}; q = deque([start]); hit = None
        while q:
            c = q.popleft()
            if c in goal: hit = c; break
            for n in self.neighbours(c):
                if n in prev: continue
                if not self.ok(*n, night, has, goal) and not (either and self.ok(*n, 1 - night, has, goal)): continue
                if both and not self.ok(*n, 1 - night, has, goal): continue
                prev[n] = c; q.append(n)
                if len(prev) > limit: break
        if hit is None: return None
        p = []; c = hit
        while c: p.append(c); c = prev[c]
        return p[::-1]
    # ------------------------------------------------------------- body
    def feet(self):
        px, py, r = self.g.pos()
        return (r, min(15, (px + 12) // 16), max(1, min(10, (py + 21) // 16)))
    HORIZON = 12        # look-ahead in game ticks (0.48 s): a player reading the telegraphs
    LOOKAHEAD = True
    def survives(self, seq):
        """roll the emulator forward with these inputs: (alive, creatures killed)"""
        g = self.g
        s = g.save(); nh = len(g.halts); lives = g.b('lives'); ok = True
        sc = int(bytes(g.block('score', 6))); room0 = g.b('cur_room')
        self.last_life = len(seq)
        for n, v in enumerate(seq):
            for _ in range(2):
                g.poke('demo_live', v); g.frame()
            if g.b('lives') < lives or g.b('p_hit') or g.b('psink') > 12: ok = False; self.last_life = n; break
        gain = int(bytes(g.block('score', 6))) - sc
        # progress towards the current waypoint; backing out of the room the
        # wrong way is heavily penalised (the room would re-spawn its creatures)
        tr, tx, ty = getattr(self, 'target', (room0, g.b('px'), g.b('py')))
        room = g.b('cur_room')
        if room != room0: prog = 0 if room == tr else -2000
        else: prog = -(abs(g.b('px') - tx) + abs(g.b('py') - ty))
        g.load(s); del g.halts[nh:]
        self.last_prog = prog
        return ok, gain
    def danger(self):
        g = self.g; S = g.S; px, py = g.b('px'), g.b('py')
        if g.b('mare_here') or g.b('clod_on') or g.b('leeched') or g.b('psink'): return True
        for i in range(3):
            b = S['enemies'] + 12 * i
            if g.mem[b] in (1, 2) and abs(g.mem[b + 2] - px) < 90 and abs(g.mem[b + 3] - py) < 90: return True
        return False
    def choose(self, v, v2):
        H = self.HORIZON
        cands = []
        if v2 is not None: cands.append([v2] + [0] * (H - 1))
        cands.append([v] * H)
        for c in ([F] + [0] * (H - 1), [R, F] + [0] * (H - 2), [L, F] + [0] * (H - 2),
                  ([F] + [0] * 6) * 2, [R, F] + [0] * 6 + [F] + [0] * 6, [L, F] + [0] * 6 + [F] + [0] * 6):
            cands.append(c)
        for m in (U, D, L, R, 0):                # line up, face, swing
            for k in (2, 4, 6, 8):
                for o in (R, L):
                    cands.append(([m] * k + [o, F] + [0] * H)[:H])
        for d in (U, D, L, R):
            cands.append([d] * H)
            cands.append([d] * 4 + [0] * (H - 4))
        cands.append([0] * H)
        best = None; longest = None
        for i, c in enumerate(cands):
            if c[0] & F and self.g.b('pfire_prev'): c = [0] + c[:-1]
            ok, gain = self.survives(c)
            if not ok:
                if longest is None or self.last_life > longest[0]: longest = (self.last_life, c[0])
                continue
            if i <= 1: return c[0]                   # the plan (or the reflex) is safe: keep going
            sc = gain * 2 + self.last_prog
            if best is None or sc > best[0]: best = (sc, c[0])
        if best is not None: return best[1]
        self.stuck_danger = getattr(self, 'stuck_danger', 0) + 1
        return longest[1]                        # nothing is safe: put it off for as long as possible
    def step(self, v):
        """one tick of input, with reflexes layered on top"""
        g = self.g
        v2 = self.reflex()
        if self.LOOKAHEAD and self.danger():
            v = self.choose(v, v2)
        elif v2 is not None: v = v2
        if v & F and g.b('pfire_prev'): v = v & ~F     # fire is edge-triggered
        lives = g.b('lives'); room = g.b('cur_room')
        self.last_v = v
        self.run(v, 2)
        if g.b('lives') < lives:
            cause = self.last_threat or 'bog/unknown'
            self.log['deaths'].append(dict(tick=g.w('gtick'), room=room, region=NAMES[(g.mem[g.S['g_desc']] >> 4) & 7],
                                           cause=cause, night=g.b('night'), lives_left=g.b('lives')))
            print('  DEATH #%d in room %d (%s) cause %s night %d' % (len(self.log['deaths']), room,
                  self.log['deaths'][-1]['region'], cause, g.b('night')))
        if g.b('cur_room') != room:
            # room_load can straddle a frame: let the generator finish
            # before anything reads the room buffer
            t = g.w('gtick')
            while g.w('gtick') == t: self.run(0, 1)
            self.log['rooms'].append(g.b('cur_room'))
    def reflex(self):
        g = self.g; S = g.S
        px, py = g.b('px'), g.b('py'); pcx, pcy = px + 12, py + 14
        self.last_threat = None
        if g.b('leeched'):
            self.last_threat = 'leech'
            return F if g.b('pattack') == 0 else 0
        best = None
        names = ['wisp', 'toad', 'adder', 'heron', 'leech', 'boggart', 'monk', 'bog-body', 'ox', 'night hag']
        for i in range(3):
            base = S['enemies'] + 12 * i
            st, t, ex, ey = g.mem[base], g.mem[base + 1], g.mem[base + 2], g.mem[base + 3]
            if st != 2: continue
            w = 24 if t == 8 else 16
            ecx, ecy = ex + w // 2, ey + w // 2
            dx, dy = ecx - pcx, ecy - pcy
            d = abs(dx) + abs(dy)
            edx, edy = g.mem[base + 4], g.mem[base + 5]
            edx = edx - 256 if edx > 127 else edx; edy = edy - 256 if edy > 127 else edy
            # a lunge/charge coming at him off his row: sidestep it
            if edy and abs(edy) >= 3 and abs(dx) < 26 and (dy > 0) == (edy < 0) and abs(dy) < 90:
                self.last_threat = names[t] if t < 10 else '?'
                return self.side(dx)
            if best is None or d < best[0]: best = (d, dx, dy, t)
        names = ['wisp', 'toad', 'adder', 'heron', 'leech', 'boggart', 'monk', 'bog-body', 'ox', 'night hag']
        if g.b('clod_on'):
            dx, dy = g.b('clod_x') + 4 - pcx, g.b('clod_y') + 4 - pcy
            if best is None or abs(dx) + abs(dy) < best[0]: best = (abs(dx) + abs(dy), dx, dy, 'clod')
        if g.b('mare_here'):
            dx, dy = g.b('mare_x') + 16 - pcx, g.b('mare_y') + 12 - pcy
            if best is None or abs(dx) + abs(dy) < best[0] + 20: best = (abs(dx) + abs(dy), dx, dy, 'mare')
        if best is None: return None
        d, dx, dy, t = best
        self.last_threat = t if isinstance(t, str) else names[t]
        if t == 8:                                  # the ox: just keep out of its row
            if abs(dy) < 20 and abs(dx) < 90:
                return U if dy > 0 and py > 8 else D
            return None
        reach = 40 if t == 'mare' else 34
        if abs(dy) < 16 and abs(dx) < reach:
            face = 2 if dx > 0 else 3
            if g.b('pattack'): return 0
            if g.b('pface') != face: return R if face == 2 else L
            return F
        return None
    def side(self, dx):
        """step sideways away from something at horizontal offset dx"""
        px = self.g.b('px')
        if dx > 0 and px > 8: return L
        if dx <= 0 and px < 224: return R
        return R if dx > 0 else L
    def push_to(self, node, room):
        """walk the feet onto node (same room)"""
        g = self.g
        _, x, y = node
        tgx, tgy = x * 16 - 4, y * 16 - 14
        tgx = max(0, min(232, tgx)); tgy = max(0, min(152, tgy))
        self.target = (room, tgx, tgy)
        px, py, _ = g.pos()
        if (px, py) == (tgx, tgy): return True
        v = 0
        if px != tgx and abs(py - tgy) <= 2: v = R if px < tgx else L
        if v == 0 and py != tgy: v = D if py < tgy else U
        if v == 0: v = R if px < tgx else L
        self.step(v)
        return False
    def cross(self, a, b):
        """leave room a.r towards b (neighbouring room)"""
        ra, rb = a[0], b[0]
        v = R if rb == ra + 1 else L if rb == ra - 1 else D if rb == ra + 16 else U
        px, py, _ = self.g.pos()
        self.target = (rb, px, py)
        self.step(v)
    # ------------------------------------------------------------- planning
    def refresh(self):
        self.livebuf = self.buf()
    def go(self, goal, label, max_ticks=20000):
        """walk until the feet are on a goal node.  Waits for the other phase
        when only that one has a route.  Returns True on arrival."""
        g = self.g
        t_end = g.w('gtick') + max_ticks if False else None
        start_ticks = self.ticks()
        stuck = 0; last = None
        while True:
            if g.b('lives') == 0 or self.game_over(): return False
            if self.ticks() - start_ticks > max_ticks: print('  give up', label); return False
            self.refresh()
            here = self.feet()
            if here in goal: return True
            night = g.b('night'); has = self.has()
            p = self.bfs(here, goal, night, has)
            if p is None:
                # route only in the other phase? walk the part that is safe in both, then wait
                p2 = self.bfs(here, goal, 1 - night, has)
                if p2 is None:
                    # the route needs both phases (e.g. causeway by day, lilies by night):
                    # plan on tiles passable in either, walk what is open now, then wait
                    p2 = self.bfs(here, goal, night, has, either=True)
                    if p2 is None:
                        self.noroute = getattr(self, 'noroute', 0) + 1
                        if self.noroute < 20:
                            for _ in range(5): self.step(0)
                            continue
                        print('  no route to', label, 'from', here, 'night', night); return False
                    k = 0
                    while k + 1 < len(p2) and self.ok(*p2[k + 1], night, has): k += 1
                    if k > 0:
                        self.follow(p2[:k + 1], 400)
                        if self.feet() != p2[k]: continue
                    self.wait_phase(label)
                    continue
                k = 0
                while k + 1 < len(p2) and self.ok(*p2[k + 1], night, has) and self.ok(*p2[k + 1], 1 - night, has): k += 1
                target = p2[k]
                if here != target:
                    self.follow(p2[:k + 1], 400)
                    continue
                self.wait_phase(label)
                continue
            self.follow(p, 600)
            pos = g.pos()
            if pos == last: stuck += 1
            else: stuck = 0
            last = pos
            if stuck > 3:
                for _ in range(8): self.step([R, L, U, D][(stuck + _) % 4])
    def follow(self, p, budget):
        """execute a path until the room changes, it ends, or the budget runs out"""
        g = self.g
        room = g.b('cur_room'); n0 = g.b('night')
        i = 1; used = 0
        while i < len(p) and used < budget:
            if g.b('cur_room') != room or g.b('night') != n0: return
            if g.b('lives') == 0 or self.game_over(): return
            a, b = p[i - 1], p[i]
            if b[0] != room:
                self.cross(a, b); used += 1; continue
            if self.push_to(b, room):
                i += 1
            used += 1
            # re-plan if knocked back (death respawn)
            if g.b('pinv') == 49: return
    def wait_phase(self, label):
        g = self.g; n0 = g.b('night'); t0 = self.ticks()
        print('  waiting for %s at room %d for %s (clock %d)' % ('day' if n0 else 'night', g.b('cur_room'), label, g.w('clock')))
        self.log['waits'].append(dict(room=g.b('cur_room'), for_=label, night=n0, clock=g.w('clock')))
        while g.b('night') == n0:
            if g.b('lives') == 0 or self.game_over(): return
            self.step(0)
        for _ in range(4): self.step(0)        # let the room re-generate for the new phase
        print('  phase changed after %d ticks' % (self.ticks() - t0))
    def ticks(self): return self.g.w('gtick')
    def game_over(self): return self.g.b('game_won') or self.g.b('lives') == 0
    # ------------------------------------------------------------- quest
    def item_goal(self, room):
        it = P.item_at(room)
        return {(room, it[0], it[1])}
    def bridle(self):
        g = self.g
        for _ in range(4000):
            if g.b('game_won'): return True
            if g.b('lives') == 0: return False
            if not g.b('mare_here'): self.step(0); continue
            mx, my = g.b('mare_x'), g.b('mare_y'); px, py, _ = g.pos()
            if abs(my - py) > 6:
                self.step(D if my > py else U); continue
            face_right = mx + 16 > px + 12
            blade = px + 24 if face_right else px - 8
            if mx - 4 <= blade <= mx + 36 and g.b('pattack') == 0:
                if g.b('pface') != (2 if face_right else 3): self.run(R if face_right else L, 2); continue
                self.run(F, 2); continue
            self.step(R if face_right else L)
        return False

def main():
    w = Walker(); g = w.g
    if '--reflex-only' in sys.argv: w.LOOKAHEAD = False
    if '--horizon' in sys.argv: w.HORIZON = int(sys.argv[sys.argv.index('--horizon') + 1])
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''
    g.frame(60); w.run(0, 20)
    print('NORMAL MODE walk: no god, no warps, no clock cheats')
    t0 = time.time()
    order = ['bit', 'lantern', 'rein', 'key', 'buckle', 'lever', 'headstall']
    for name in order:
        room = QUEST[name]
        w.event('-> %s (room %d)' % (name, room))
        ok = w.go(w.item_goal(room), name)
        for _ in range(10): w.step(0)
        w.event(('got ' if ok and w.taken(room) else 'FAILED ') + name)
        if not ok: break
    if g.b('bridle') == 15:
        w.event('-> Mare\'s Isle')
        isle = {(ISLE_HOME, x, y) for x in range(2, 14) for y in range(2, 10)}
        if w.go(isle, 'isle'):
            w.event('on the Isle')
            # by day she waits here; at night she is out hunting: wait for day
            if g.b('night'): w.wait_phase('the Mare at home')
            w.bridle()
    w.event('bridled' if g.b('game_won') else 'run ended')
    for _ in range(400): w.run(0, 1)
    w.event('ending done')
    for _ in range(900): w.run(0, 1)
    res = dict(horizon=w.HORIZON if w.LOOKAHEAD else 0, won=bool(g.b('game_won')), lives_left=g.b('lives'), deaths=w.log['deaths'],
               ticks=w.ticks(), minutes=round(w.ticks() / 25 / 60, 1), waits=w.log['waits'],
               pct=g.b('go_pct'), rooms_walked=len(w.log['rooms']), events=w.events, wall_s=round(time.time() - t0))
    json.dump(res, open(os.path.join(ROOT, 'build/walk_log%s.json' % ('_' + tag if tag else '')), 'w'), indent=1)
    print('RESULT won=%s lives_left=%d deaths=%d game time %.1f min, %d screen changes, pct %d' % (
        res['won'], res['lives_left'], len(res['deaths']), res['minutes'], res['rooms_walked'], res['pct']))
    if '--stream' in sys.argv:
        import bot
        bot.write(w)

if __name__ == '__main__':
    main()
