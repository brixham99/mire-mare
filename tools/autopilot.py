#!/usr/bin/env python3
"""autopilot.py - plays the slice in the headless core with a BFS path planner
(closed loop on the real game state) and records the per-frame key timeline,
so the same session can be replayed into Fuse with xdotool."""
import sys, os, json
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import Game

class Pilot:
    def __init__(self, g):
        self.g = g; S = g.S
        self.flags = [g.mem[S['tile_flags'] + i] for i in range(32)]
        self.timeline = []          # (frame, keystring)
        self.frame_no = 0; self.cur = ''
    def room(self):
        rb = self.g.S['roombuf']; return [self.g.mem[rb + i] for i in range(176)]
    def tf(self, room, x, y):
        return self.flags[room[(y >> 4) * 16 + (x >> 4)]]
    def free(self, room, x, y):
        for fx, fy in ((x+6, y+18), (x+17, y+18), (x+6, y+23), (x+17, y+23)):
            if self.tf(room, fx, fy) & 1: return False
        return True
    def plan(self, goal):
        g = self.g; room = self.room()
        sx, sy = g.b('px'), g.b('py')
        start = (sx, sy); prev = {start: None}; q = deque([start])
        while q:
            p = q.popleft()
            if goal(*p):
                path = []
                while prev[p]: p, k = prev[p]; path.append(k)
                return path[::-1]
            x, y = p
            for k, dx, dy in (('W', 2, 0), ('Q', -2, 0), ('E', 0, 2), ('R', 0, -2)):
                n = (x + dx, y + dy)
                if not (0 <= n[0] <= 232 and 0 <= n[1] <= 152) or n in prev: continue
                if not self.free(room, *n): continue
                if self.tf(room, n[0] + 12, n[1] + 21) & 4: continue     # keep out of deep bog
                prev[n] = (p, k); q.append(n)
        return None
    def set_keys(self, keys):
        g = self.g
        for k in self.cur:
            if k not in keys: g.press(k, False)
        for k in keys:
            if k not in self.cur: g.press(k, True)
        if keys != self.cur: self.timeline.append((self.frame_no, keys))
        self.cur = keys
    def step(self, keys, n=1):
        self.set_keys(keys)
        for _ in range(n): self.g.frame(); self.frame_no += 1
    def enemy_near(self):
        g = self.g; e = g.S['enemies']; px, py = g.b('px'), g.b('py')
        for i in range(3):
            st, ty, ex, ey = (g.mem[e + i*10 + k] for k in range(4))
            if st == 2 and abs((ey + 8) - (py + 14)) < 12:
                d = (ex + 8) - (px + 12)
                if 6 < abs(d) < 26: return 'W' if d > 0 else 'Q'
        return None
    def go(self, goal, then=None, limit=1500):
        """walk until goal(x,y) holds; replans every tick; swings at enemies"""
        for _ in range(limit):
            g = self.g
            x, y = g.b('px'), g.b('py')
            if goal(x, y): break
            side = self.enemy_near()
            if side and g.b('pattack') == 0 and g.b('pinv') == 0:
                self.step(side, 2); self.step(side + 'T', 2); self.step('', 6); continue
            path = self.plan(goal)
            if not path: self.step('', 2); continue
            self.step(path[0], 2)
        if then:
            room = g.b('cur_room')
            for _ in range(20):
                self.step(then, 2)
                if g.b('cur_room') != room: break
        self.step('', 2)

def gem_goal(p, tx, ty): return lambda x, y: (x + 12) >> 4 == tx and (y + 21) >> 4 == ty

def run(save=None):
    g = Game(); p = Pilot(g)
    g.frame(100); g.press('SPACE'); g.frame(40); g.press('SPACE', False); g.frame(20)
    p.step('1', 4); p.step('', 10)
    p.timeline = []; p.frame_no = 0
    p.step('0', 4); p.step('', 30)
    log = []
    def mark(name): log.append((name, p.frame_no, g.pos(), g.b('gems'), g.b('lives')))
    mark('start')
    # F -> E: exit left on tile rows 4-6
    p.go(lambda x, y: x == 0 and 50 <= y <= 84, then='Q'); mark('in E')
    p.go(gem_goal(p, 11, 5)); mark('E gem')
    p.go(lambda x, y: y == 152 and 98 <= x <= 128, then='E'); mark('in I')
    p.go(gem_goal(p, 12, 5)); mark('I gem')
    p.go(lambda x, y: x == 232 and 50 <= y <= 84, then='W'); mark('in J')
    p.go(gem_goal(p, 11, 7)); mark('J gem')
    p.go(lambda x, y: x == 232 and 50 <= y <= 84, then='W'); mark('in K')
    p.go(gem_goal(p, 13, 9)); mark('K gem')
    for m in log: print(m)
    if save:
        json.dump({'timeline': p.timeline, 'frames': p.frame_no, 'log': log}, open(save, 'w'))
    return g, p, log

if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'build/demo_timeline.json')
