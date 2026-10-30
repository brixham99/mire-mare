#!/usr/bin/env python3
"""fuse_pilot.py - closed-loop bot that plays the slice *inside Fuse* (Nathan's
48K ROM, tape loaded through the ROM's LOAD "").  Every ~40 ms it grabs the Fuse
window, works out which room is showing and where Sabreman is (by diffing the
screen against clean room renders taken from the headless core), plans a path
with BFS and holds the matching key via xdotool.  ffmpeg records the session.
Run: python3 tools/fuse_pilot.py   ->  build/fuse_pilot.mp4, build/fuse_pilot_log.json"""
import sys, os, time, json, subprocess
import numpy as np
from collections import deque
from PIL import ImageGrab
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import Game
from fusectl import Fuse, ENV
from rompath import ROM48
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- 1. clean room templates + maps from the headless core
def screen_bits(mem, base):
    a = np.zeros((192, 256), bool)
    for y in range(192):
        off = ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
        row = bytes(mem[base + off + c] for c in range(32))
        a[y] = np.unpackbits(np.frombuffer(row, np.uint8)).astype(bool)
    return a

def templates():
    g = Game(); S = g.S
    g.frame(100); g.press('SPACE'); g.frame(40); g.press('SPACE', False); g.frame(20)
    g.tap('0'); g.frame(20)
    flags = [g.mem[S['tile_flags'] + i] for i in range(32)]
    T = {}
    for r in range(12):
        # roombuf of the start room has an open left edge: fake the room number
        for k in range(3): g.mem[S['enemies'] + 10*k] = 0
        for row in (4, 5, 6): g.mem[S['roombuf'] + row*16] = 0     # open the left edge
        g.mem[S['cur_room']] = r + 1; g.mem[S['px']] = 0; g.mem[S['py']] = 66
        g.press('Q')
        for _ in range(30):
            g.frame()
            if g.b('cur_room') == r: break
        g.press('Q', False); g.frame(12)
        assert g.b('cur_room') == r, (r, g.b('cur_room'))
        room = [g.mem[S['roombuf'] + i] for i in range(176)]
        T[r] = (screen_bits(g.mem, 0xE000)[16:192], room)
    return T, flags

class Planner:
    def __init__(self, flags): self.flags = flags
    def tf(self, room, x, y): return self.flags[room[(y >> 4) * 16 + (x >> 4)]]
    def free(self, room, x, y):
        return all(not (self.tf(room, fx, fy) & 1) for fx, fy in ((x+6, y+18), (x+17, y+18), (x+6, y+23), (x+17, y+23)))
    def snap(self, room, x, y):
        x, y = max(0, min(232, x & ~1)), max(0, min(152, y & ~1))
        for r in range(0, 12, 2):
            for dx in range(-r, r + 1, 2):
                for dy in range(-r, r + 1, 2):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx <= 232 and 0 <= ny <= 152 and self.free(room, nx, ny): return nx, ny
        return x, y
    def plan(self, room, start, goal):
        prev = {start: None}; q = deque([start])
        while q:
            p = q.popleft()
            if goal(*p):
                path = []
                while prev[p]: p, k = prev[p]; path.append(k)
                return path[::-1]
            x, y = p
            for k, dx, dy in (('w', 2, 0), ('q', -2, 0), ('e', 0, 2), ('r', 0, -2)):
                n = (x + dx, y + dy)
                if not (0 <= n[0] <= 232 and 0 <= n[1] <= 152) or n in prev: continue
                if not self.free(room, *n): continue
                if self.tf(room, n[0] + 12, n[1] + 21) & 4: continue
                prev[n] = (p, k); q.append(n)
        return None

# ---------- 2. reading the Fuse screen
class Eye:
    def __init__(self, f, T, flags):
        self.f, self.T, self.flags = f, T, flags
        self.box = (f.x + 32, f.y + 24, f.x + 32 + 256, f.y + 24 + 192)
    def grab(self):
        im = np.asarray(ImageGrab.grab(bbox=self.box, xdisplay=ENV['DISPLAY']).convert('RGB'))
        return im
    def look(self):
        im = self.grab()
        lit = im.max(axis=2)[16:192] > 64
        best = None
        for r, (tb, room) in self.T.items():
            gm = self.gemmask(room)
            d = (lit ^ tb) & ~gm
            n = int(d.sum())
            if best is None or n < best[0]: best = (n, r, d)
        n, r, d = best
        return r, d, im
    def gemmask(self, room):
        m = np.zeros((176, 256), bool)
        for i, t in enumerate(room):
            if self.flags[t] & 24: m[(i >> 4) * 16:(i >> 4) * 16 + 16, (i & 15) * 16:(i & 15) * 16 + 16] = True
        return m
    @staticmethod
    def blobs(d):
        # 4x4 block grid, flood fill
        h, w = d.shape
        g = d.reshape(h // 4, 4, w // 4, 4).any(axis=(1, 3))
        seen = np.zeros_like(g); out = []
        for y0, x0 in zip(*np.nonzero(g)):
            if seen[y0, x0]: continue
            st = [(y0, x0)]; seen[y0, x0] = True; cells = []
            while st:
                y, x = st.pop(); cells.append((y, x))
                for yy in range(y - 1, y + 2):
                    for xx in range(x - 1, x + 2):
                        if 0 <= yy < g.shape[0] and 0 <= xx < g.shape[1] and g[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True; st.append((yy, xx))
            ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
            sub = d[min(ys)*4:max(ys)*4+4, min(xs)*4:max(xs)*4+4]
            yy, xx = np.nonzero(sub)
            out.append((min(xs)*4 + xx.min(), min(ys)*4 + yy.min(), min(xs)*4 + xx.max(), min(ys)*4 + yy.max(), len(yy)))
        return out

def main():
    T, flags = templates(); P = Planner(flags)
    f = Fuse(os.path.join(ROOT, 'build/miremare.tap'), ['--rom-48', ROM48, '--traps', '--fastload', '--no-auto-load'])
    xd = lambda *a: subprocess.run(['xdotool', *a], env=ENV)
    time.sleep(3); f.key('j'); time.sleep(.3)
    for _ in range(2):
        xd('keydown', 'Control_L'); f.key('p'); xd('keyup', 'Control_L'); time.sleep(.3)
    f.key('Return'); time.sleep(1); f.key('F8'); time.sleep(10)
    xd('keydown', 'space'); time.sleep(0.8); xd('keyup', 'space'); time.sleep(0.4)
    xd('keydown', '1'); time.sleep(0.1); xd('keyup', '1'); time.sleep(0.4)
    eye = Eye(f, T, flags)
    rec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'x11grab', '-framerate', '50',
                            '-video_size', f'{f.w}x{f.h}', '-i', f'{ENV["DISPLAY"]}+{f.x},{f.y}',
                            '-t', '75', '-c:v', 'libx264', '-preset', 'ultrafast', '-qp', '0',
                            os.path.join(ROOT, 'build/fuse_pilot.mp4')], env=ENV)
    time.sleep(1.0); t0 = time.perf_counter()
    f.key('0', 0.12); time.sleep(0.6)
    held = None; log = []
    def hold(k):
        nonlocal held
        if k == held: return
        if held: xd('keyup', held)
        if k: xd('keydown', k)
        held = k
    def gem(tx, ty): return lambda x, y: (x + 12) >> 4 == tx and (y + 21) >> 4 == ty
    plan = [('exit', lambda x, y: x == 0 and 50 <= y <= 84, 'q', 4),
            ('gem', gem(11, 5), None, 4),
            ('exit', lambda x, y: y == 152 and 98 <= x <= 128, 'e', 8),
            ('gem', gem(12, 5), None, 8),
            ('exit', lambda x, y: x == 232 and 50 <= y <= 84, 'w', 9),
            ('gem', gem(11, 7), None, 9),
            ('exit', lambda x, y: x == 232 and 50 <= y <= 84, 'w', 10),
            ('gem', gem(13, 9), None, 10)]
    stage = 0; last = None; swing_until = 0
    while stage < len(plan) and time.perf_counter() - t0 < 70:
        r, d, im = eye.look()
        name, goal, exit_key, want_room = plan[stage]
        room = T[r][1]
        bl = Eye.blobs(d)
        big = [b for b in bl if b[2] - b[0] >= 13 and b[3] - b[1] >= 17]
        now = time.perf_counter() - t0
        if name == 'exit' and r == want_room:
            log.append(('entered room', r, round(now, 2))); stage += 1; hold(None); continue
        if not big:
            hold(held); time.sleep(0.02); continue                    # blinking / sprite hidden
        b = max(big, key=lambda b: b[4])
        x, y = P.snap(room, int(b[0]) - 2, int(b[3]) - 23)
        if name == 'gem' and (goal(x, y) or r != want_room):
            log.append(('gem reached', r, (x, y), round(now, 2))); stage += 1; continue
        # enemies: small blobs level with Sabreman and close -> swing at them
        for e in bl:
            if e is b or e[4] < 12: continue
            ex, ey = (e[0] + e[2]) // 2, (e[1] + e[3]) // 2
            if abs(ey - (y + 14)) < 12 and 8 < abs(ex - (x + 12)) < 28 and now > swing_until:
                k = 'w' if ex > x + 12 else 'q'
                hold(k); time.sleep(0.05); hold('t'); time.sleep(0.1); hold(None)
                swing_until = now + 0.6; log.append(('swing', r, round(now, 2)))
                break
        path = P.plan(room, (x, y), goal)
        if path is None:
            if name == 'exit' and goal(x, y): hold(exit_key)
            else: hold(None)
        elif not path:
            hold(exit_key)
        else:
            hold(path[0])
        time.sleep(0.03)
    hold(None)
    log.append(('done', stage, round(time.perf_counter() - t0, 2)))
    time.sleep(2); f.shot(os.path.join(ROOT, 'shots/fuse_pilot_end.png'))
    rec.terminate(); rec.wait()
    f.close()
    json.dump(log, open(os.path.join(ROOT, 'build/fuse_pilot_log.json'), 'w'), indent=1, default=int)
    for l in log: print(l)

if __name__ == '__main__':
    main()
