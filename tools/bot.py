#!/usr/bin/env python3
"""bot.py - plays the DEMO build headless in 'live' mode and records the
exact per-tick input stream, which build.sh demo then embeds so the same
run replays tick-for-tick in Fuse on the real ROM.

The verification route (cheat commands are marked *):
  Sedge Fen start -> walk a screen -> *warp to each quest room in turn and
  WALK to its item (Bit, lantern, Rein, key, Buckle, lever, Headstall),
  night (*clock) on the Mere, wait for the roaming Mare, dawn (*clock),
  Mare's Isle by day, bridle her with the sabre -> ending -> rating.
*god mode is on throughout (enemies cannot cost lives).
Writes build/demo_stream.asm and build/bot_events.json."""
import json, os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(__file__))
from headless import Game, ROOT

R, L, D, U, F = 1, 2, 4, 8, 16
class Bot:
    def __init__(self):
        import worldcache
        self.W = worldcache.load()     # may run the Z80 generator: do it before the game core is loaded
        self.g = Game('miremare_live')
        self.stream = []          # list of ('in', v, n) / ('cmd', bytes)
        self.events = []
        self.flags = list(self.g.block('tile_flags', 37))
        self.T = {}
        for line in open(os.path.join(ROOT, 'data/tiles.asm')):
            if line.startswith('TILE_'):
                k, _, v = line.split(); self.T[k[5:]] = int(v)
    # ---- low level
    def reads(self): return self.g.w('demo_reads')
    def run(self, v, frames=1):
        g = self.g
        for _ in range(frames):
            g.poke('demo_live', v); r0 = self.reads(); g.frame(); n = self.reads() - r0
            if n: self.log_in(v, n)
    def log_in(self, v, n):
        if self.stream and self.stream[-1][0] == 'in' and self.stream[-1][1] == v:
            self.stream[-1] = ('in', v, self.stream[-1][2] + n)
        else:
            self.stream.append(('in', v, n))
    def cmd(self, c, args=()):
        g = self.g
        for i, a in enumerate(args): g.poke('demo_args', a, i)
        g.poke('demo_live', c)
        r0 = self.reads()
        for _ in range(3000):
            g.frame()
            n = self.reads() - r0
            if n: break
        else:
            raise RuntimeError('command $%02X never consumed (pc %04X room %d)' % (c, g.pc(), g.b('cur_room')))
        self.stream.append(('cmd', bytes([c] + list(args))))
        if n > 1: self.log_in(0, n - 1)
        # live mode returned 0 for the command tick and clears demo_live
    def event(self, name):
        self.events.append(dict(name=name, frame=len(self.g.halts), tick=self.g.w('gtick'),
                                room=self.g.b('cur_room')))
        print('%-28s frame %6d room %3d pos %s lives %d' % (name, len(self.g.halts), self.g.b('cur_room'),
                                                         self.g.pos()[:2], self.g.b('lives')))
    def shot(self, name): self.g.shot(os.path.join(ROOT, 'shots/h_%s.png' % name))
    # ---- room knowledge (live roombuf)
    def buf(self): return list(self.g.block('roombuf', 176))
    def ok_tile(self, t, allow_item=True):
        f = self.flags[t]
        if f & 1: return False
        if t == self.T['BOG']: return False
        return True
    def feet_tile(self):
        px, py, _ = self.g.pos()
        return (px + 12) // 16, (py + 21) // 16
    def path(self, goal, allow_bog_goal=True):
        buf = self.buf(); start = self.feet_tile()
        prev = {start: None}; q = deque([start])
        while q:
            c = q.popleft()
            if c == goal: break
            x, y = c
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if not (0 <= n[0] < 16 and 1 <= n[1] < 11) or n in prev: continue
                t = buf[n[1] * 16 + n[0]]
                if self.ok_tile(t) or (n == goal and allow_bog_goal):
                    prev[n] = c; q.append(n)
        if goal not in prev: return None
        p = []; c = goal
        while c: p.append(c); c = prev[c]
        return p[::-1]
    def goto_px(self, tx, ty, timeout=400):
        """walk the feet into tile (tx,ty)"""
        p = self.path((tx, ty))
        if p is None: raise RuntimeError('no path to %s in room %d' % ((tx, ty), self.g.b('cur_room')))
        room = self.g.b('cur_room')
        for (x, y) in p[1:]:
            tgx, tgy = x * 16 - 4, y * 16 - 14
            for _ in range(timeout):
                if self.g.b('cur_room') != room: return
                px, py, _ = self.g.pos()
                if (px, py) == (tgx, tgy) or (self.feet_tile() == (x, y) and (x, y) == p[-1]): break
                v = 0
                if px != tgx and abs(py - tgy) <= 2 and px != tgx:
                    v = R if px < tgx else L
                if py != tgy and (v == 0):
                    v = D if py < tgy else U
                if v == 0: v = R if px < tgx else L
                self.run(v, 1)
            else:
                raise RuntimeError('stuck going to %s at %s room %d' % ((x, y), self.g.pos(), room))
    def walk_exit(self, d, timeout=600):
        """walk out of the room through exit d (N/S/E/W)"""
        room = self.g.b('cur_room')
        gx, gy = {'N': (7, 1), 'S': (7, 10), 'W': (0, 5), 'E': (15, 5)}[d]
        self.goto_px(gx, gy)
        v = {'N': U, 'S': D, 'W': L, 'E': R}[d]
        for _ in range(timeout):
            if self.g.b('cur_room') != room: return
            self.run(v, 1)
        raise RuntimeError('could not leave room %d by %s' % (room, d))
    def spot(self, room_buf, near=(8, 5)):
        best = None
        for ty in range(2, 10):
            for tx in range(1, 15):
                ok = all(self.ok_tile(room_buf[ty * 16 + tx + dx]) and not self.flags[room_buf[ty * 16 + tx + dx]] & 8
                         for dx in (0, 1)) and self.ok_tile(room_buf[(ty - 1) * 16 + tx])
                if ok:
                    d = abs(tx - near[0]) + abs(ty - near[1])
                    if best is None or d < best[0]: best = (d, tx, ty)
        return best[1:] if best else None
    def warp(self, room, near=(8, 5)):
        # generate the room to find a spot: warp to it first at its centre is not
        # safe, so look at the room through a scratch warp-free read: use cache
        buf = self.W[room]['buf']
        if self.g.b('night'):
            buf = [self.T['LILYPAD'] if t in (self.T['NIGHTLILY'], self.T['CAUSEWAYSUNK']) else t for t in buf]
        s = self.spot(buf, near)
        if not s: raise RuntimeError('no spot in room %d' % room)
        tx, ty = s
        self.cmd(0x80, (room, tx * 16 - 4, ty * 16 - 14))
        self.run(0, 4)
        if self.g.b('cur_room') != room: raise RuntimeError('warp to %d failed' % room)
    def item_tile(self):
        return self.g.b('item_tx'), self.g.b('item_ty')
    def fetch_item(self, name):
        tx, ty = self.item_tile()
        if tx == 255: raise RuntimeError('no item in room %d' % self.g.b('cur_room'))
        self.event('approach ' + name)
        self.goto_px(tx, ty)
        for _ in range(10): self.run(0, 1)
        self.event('got ' + name)

def main():
    b = Bot(); g = b.g
    g.frame(60)
    b.run(0, 20)
    b.event('start Sedge Fen'); b.shot('v_start')
    b.cmd(0x83)                                 # god mode
    b.walk_exit('N'); b.run(0, 30); b.event('walked to next screen'); b.shot('v_fen_walk')
    quests = [('bit', 144, 'v_fen'), ('lantern', 20, 'v_wood'), ('rein', 0, 'v_wood2'),
              ('key', 63, 'v_hags'), ('buckle', 159, 'v_hags2'), ('lever', 24, 'v_abbey_crypt'),
              ('headstall', 10, 'v_abbey')]
    for name, room, shot in quests:
        b.warp(room)
        b.run(0, 10)
        b.shot(shot)
        b.fetch_item(name)
        b.run(0, 120)                           # message box
        b.shot(shot + '_after')
    assert g.b('bridle') == 15, g.b('bridle')
    # a marsh-light and a mire-bloom on the way? (just show them in shots)
    # ---- night on the Mere
    b.cmd(0x81); b.run(0, 80)
    b.event('nightfall'); b.shot('v_night')
    b.warp(86)                                  # (6,5) the Mere, by the Isle
    b.run(0, 10); b.shot('v_mere_night')
    for i in range(1200):
        b.run(0, 1)
        if g.b('mare_here'): break
    b.event('mare arrives'); 
    for i in range(150):
        b.run(0, 1)
        if i == 40: b.shot('v_mare')
    # ---- dawn: she goes home; bridle her on the Isle
    b.cmd(0x81); b.run(0, 80); b.event('dawn')
    b.warp(104, near=(3, 5))
    b.run(0, 10); b.event('Mare\'s Isle'); b.shot('v_isle')
    for i in range(3000):
        if g.b('game_won'): break
        mx, my = g.b('mare_x'), g.b('mare_y')
        px, py, _ = g.pos()
        v = 0
        here = g.b('mare_here')
        if not here:
            b.run(0, 1); continue
        # stand still in her row and swing when she is in reach
        face_right = mx + 16 > px + 12
        blade = px + 24 if face_right else px - 8
        if abs(my - py) < 14 and mx - 4 <= blade <= mx + 36 and g.b('pattack') == 0:
            want = R if face_right else L
            if g.b('pface') != (2 if face_right else 3):
                b.run(want, 1); continue
            b.run(F, 1); b.run(0, 1); continue
        b.run(0, 1)
    b.event('bridled' if g.b('game_won') else 'FAILED to bridle')
    for i in range(400):
        b.run(0, 1)
        if i == 200: b.shot('v_ending')
    b.event('ending done')
    for i in range(900):
        b.run(0, 1)
        if g.b('game_won') and i % 50 == 0: b.shot('v_rating_%03d' % i)
    write(b)

def write(b):
    out = ['; generated by tools/bot.py - verification run (%d entries)' % len(b.stream)]
    total = 0
    for e in b.stream:
        if e[0] == 'in':
            v, n = e[1], e[2]; total += n
            while n > 0:
                k = min(n, 255); out.append('        DEFB %d,%d' % (v, k)); n -= k
        else:
            out.append('        DEFB ' + ','.join('$%02X' % x for x in e[1])); total += 1
    out.append('        DEFB $FF')
    open(os.path.join(ROOT, 'build/demo_stream.asm'), 'w').write('\n'.join(out) + '\n')
    json.dump(b.events, open(os.path.join(ROOT, 'build/bot_events.json'), 'w'), indent=1)
    print('stream: %d ticks, %d lines' % (total, len(out)))

if __name__ == '__main__':
    main()
