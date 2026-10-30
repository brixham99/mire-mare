#!/usr/bin/env python3
"""test_game.py - headless assertion suite for the full Mire Mare build.
Part 1 drives the normal build (miremare.bin) through the menu.
Part 2 drives the live cheat build (miremare_live.bin) via tools/bot.Bot:
warps, clock jumps, pokes - to exercise every system directly."""
import os, sys, time, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import Game, ROOT, symbols
from bot import Bot, R, L, D, U, F
import worldcache
OK = []
def check(name, cond, info=''):
    print(('PASS ' if cond else 'FAIL ') + name + ('  ' + str(info) if info != '' else ''))
    OK.append(bool(cond))
t_start = time.time()
# ------------------------------------------------------------ memory
for stem in ('miremare', 'miremare_live', 'miremare_demo'):
    p = os.path.join(ROOT, 'build/%s.sym' % stem)
    if not os.path.exists(p): continue
    S = symbols(stem)
    check('%s fits below the screen mirror' % stem, S['end_all'] <= 0xE000, '%04X' % S['end_all'])
# ------------------------------------------------------------ part 1: normal build
g = Game(); S = g.S
g.frame(120); g.press('SPACE'); g.frame(40); g.press('SPACE', False); g.frame(10)
check('menu tune beeps', g.beeps > 0, g.beeps)
g.tap('2'); check('menu: select kempston', g.b('ctrl_type') == 1)
g.tap('1'); check('menu: select keyboard', g.b('ctrl_type') == 0)
g.tap('0'); g.frame(30)
check('game starts in Sedge Fen room 99', g.b('cur_room') == 99, g.pos())
check('5 lives, no bridle, daytime', (g.b('lives'), g.b('bridle'), g.b('night')) == (5, 0, 0))
for i in range(3): g.mem[S['enemies'] + 12 * i] = 0
x0 = g.b('px'); t0 = g.b('tick'); g.hold(['right'], 20)
dt = (g.b('tick') - t0) & 255
check('walks 2 px per tick (keyboard P)', g.b('px') - x0 == 2 * dt, (g.b('px') - x0, dt))
check('locked 25 fps in the start room', 9 <= dt <= 11, dt)
# ------------------------------------------------------------ part 2: live build
b = Bot(); g = b.g; S = g.S; T = b.T
g.frame(60); b.run(0, 10)
check('live build starts a game', g.b('cur_room') == 99)
def clear_en():
    for i in range(3): g.mem[S['enemies'] + 12 * i] = 0
def put(x, y): g.poke('px', x); g.poke('py', y)
W = b.W
WJ = json.load(open(os.path.join(ROOT, 'build/world.json')))
# --- full map sweep, day then night: every room loads, keeps 25 fps, enemy census
types = set(); slow = []; fails = []; dry = 0
b.cmd(0x83)
for night in (0, 1):
    if night: b.cmd(0x81); b.run(0, 80)
    for room in range(160):
        g.poke('clock', 0); g.poke('clock', 8, 1)        # keep clear of dusk/dawn while measuring
        try: b.warp(room)
        except Exception as e:
            if night == 0 and WJ[str(room)]['region'] == 4: dry += 1; continue   # open Mere: no dry land by day
            fails.append((room, night, str(e))); continue
        b.run(0, 6)
        for i in range(3):
            if g.mem[S['enemies'] + 12 * i]: types.add(g.mem[S['enemies'] + 12 * i + 1])
        b.run(0, 14); t0 = g.w('gtick'); b.run(0, 100); dt = g.w('gtick') - t0
        if dt < 47: slow.append((room, night, dt))
check('all 160 rooms load by warp (night), all non-Mere rooms by day', not fails, (fails[:5], 'open Mere by day: %d' % dry))
check('every room holds 25 fps (>=47 ticks per 100 frames)', not slow, slow[:8])
check('god mode kept lives during the sweep', g.b('lives') == 5, g.b('lives'))
check('all 10 enemy types appear in the world (night hags by night)', types == set(range(10)), sorted(types))
check('night: dim_mask clears BRIGHT', g.b('dim_mask') == 0xBF and g.b('night') == 1)
# --- night routes on the Mere
b.warp(86)
buf = b.buf()
check('night: lilies float (no NIGHTLILY tiles at night)', T['NIGHTLILY'] not in buf and T['LILYPAD'] in buf)
check('night: HUD shows the moon', g.mem[0x5800 + 20] & 7 == 5)
b.cmd(0x81); b.run(0, 60)
buf = b.buf()
check('dawn: lilies sink again', T['LILYPAD'] not in buf or T['NIGHTLILY'] in buf)
ft = b.feet_tile()
check('dawn on the Mere: rescued or given water-walk', g.b('pu_water') > 0 or b.ok_tile(buf[ft[1] * 16 + ft[0]]),
      (g.pos(), g.b('pu_water')))
check('dawn: Mare goes home to the Isle', g.b('mare_room') == 104, g.b('mare_room'))
# --- bog: sinking and drowning without water-walk
def find_tile(tile, room):
    bb = W[room]['buf']
    for i, t in enumerate(bb):
        if t == tile and 2 <= i // 16 <= 9 and 1 <= i % 16 <= 14: return i % 16, i // 16
bog_room = next(r for r in range(160) if find_tile(T['BOG'], r))
tx, ty = find_tile(T['BOG'], bog_room)
b.warp(bog_room); clear_en(); g.poke('pu_water', 0)
lives = g.b('lives'); put(tx * 16 - 4, ty * 16 - 14); b.run(0, 200)
check('standing in bog drowns (a life lost)', g.b('lives') == lives - 1, (bog_room, lives, g.b('lives')))
b.warp(bog_room); clear_en(); g.poke('pu_water', 250); lives = g.b('lives')
put(tx * 16 - 4, ty * 16 - 14); b.run(0, 120)
check('water-walk bloom: no sinking', g.b('lives') == lives and g.b('psink') == 0, (g.b('lives'), g.b('psink')))
g.poke('pu_water', 0)
# --- blooms: fever, drowse, swift
b.warp(99); clear_en(); b.run(0, 5)
def moved(v, n=10):
    x0, y0 = g.b('px'), g.b('py'); b.run(v, n); return g.b('px') - x0, g.b('py') - y0
put(100, 70); g.poke('pu_fever', 100); dx, _ = moved(R); g.poke('pu_fever', 0)
check('fever bloom reverses controls', dx < 0, dx)
put(100, 70); g.poke('pu_drowse', 100); dx, _ = moved(R); g.poke('pu_drowse', 0)
check('drowse bloom freezes Sabreman', dx == 0, dx)
put(60, 70); x0 = g.b('px'); t0 = g.w('gtick'); g.poke('pu_swift', 100); b.run(R, 10)
spd = (g.b('px') - x0) / max(1, g.w('gtick') - t0); g.poke('pu_swift', 0)
check('swift bloom doubles speed', 3.5 <= spd <= 4.0, spd)
# --- items: marsh-light, re-entry
lr = next(r for r in range(160) if WJ[str(r)]['item'] == 1 and r != 99)
b.warp(lr); clear_en()
gems = g.b('gems'); b.fetch_item('marsh-light'); b.run(0, 5)
check('marsh-light collected', g.b('gems') == gems + 1, (lr, gems, g.b('gems')))
check('room flagged RF_GOT', g.mem[S['room_flags'] + lr] & 1)
b.warp(lr); check('taken item does not return', b.item_tile()[0] == 255, b.item_tile())
# --- abbey gating: spirit doors, crypt doors, causeway
sd = next(r for r in range(160) if T['SPIRITDOOR'] in W[r]['buf'])
cd = next(r for r in range(160) if T['CRYPTDOOR'] in W[r]['buf'])
b.warp(sd); check('spirit door closed without the lantern', T['SPIRITDOOR'] in b.buf())
g.poke('has_lantern', 1); b.cmd(0x81); b.run(0, 60); b.warp(sd)
check('spirit door opens at night with the lantern', T['SPIRITDOOR'] not in b.buf())
b.cmd(0x81); b.run(0, 60); b.warp(sd)
check('spirit door closed again by day', T['SPIRITDOOR'] in b.buf())
b.warp(cd); check('crypt door locked without the key', T['CRYPTDOOR'] in b.buf())
g.poke('has_key', 1); b.warp(cd); check('crypt door opens with the key', T['CRYPTDOOR'] not in b.buf())
cw = next(r for r in range(160) if T['CAUSEWAYSUNK'] in W[r]['buf'])
b.warp(cw); check('causeway sunk before the lever', T['CAUSEWAYSUNK'] in b.buf())
g.poke('causeway_up', 1); b.warp(cw); check('causeway raised by the lever', T['CAUSEWAYSUNK'] not in b.buf() and T['CAUSEWAY'] in b.buf())
# --- enemies: sabre kills a wisp, the ox cannot die
def slot(i, k): return g.mem[S['enemies'] + 12 * i + k]
def enemy_room(t):
    for r in range(160):
        try: b.warp(r)
        except RuntimeError: continue
        for n in ('pu_water', 'pu_swift', 'pu_ward', 'pu_fever', 'pu_drowse', 'leeched'): g.poke(n, 0)
        if not any(slot(i, 0) and slot(i, 1) == t for i in range(3)): continue
        b.run(0, 40)
        for i in range(3):
            if slot(i, 0) == 2 and slot(i, 1) == t: return r, i
def strike(t):
    r, i = enemy_room(t)
    for k in range(3):
        if k != i: g.mem[S['enemies'] + 12 * k] = 0
    hp0 = slot(i, 10); face = R if g.b('px') < 150 else L; hist = []
    for k in range(8):
        if slot(i, 0) != 2 or slot(i, 1) != t: break
        g.mem[S['enemies'] + 12 * i + 2] = (g.b('px') + 24) if face == R else (g.b('px') - 16)
        g.mem[S['enemies'] + 12 * i + 3] = g.b('py') + 4
        b.run(face, 2); b.run(F, 2); pa = g.b('pattack'); b.run(0, 14); hist.append((slot(i, 0), slot(i, 10), pa, g.b('px'), g.b('pface')))
    return r, hist
r, h = strike(0)
check('sabre kills a wisp', h and h[-1][0] != 2, (r, h))
r, h = strike(5)
check('a boggart takes two hits', len(h) >= 2 and h[-1][0] != 2, (r, h))
r, h = strike(8)
check('the ox survives the sabre', h and all(x[0] == 2 for x in h), (r, h))
# --- herons rear back before a (slower) lunge; a struck creature is knocked back
def solo(t):
    r, i = enemy_room(t)
    for k in range(3):
        if k != i: g.mem[S['enemies'] + 12 * k] = 0
    return r, i
r, i = solo(3); put(40, 70); b.run(0, 2)
E = S['enemies'] + 12 * i
g.mem[E + 2] = 140; g.mem[E + 3] = 70; g.mem[E + 11] = 0
xs = {}
for k in range(80):
    g.mem[E + 3] = 70; b.run(0, 1); xs.setdefault(g.b('tick'), slot(i, 2))
xv = list(xs.values()); steps = [b_ - a_ for a_, b_ in zip(xv, xv[1:])]
first = next((k for k, d in enumerate(steps) if d), None)
check('a heron rears for 8+ ticks before lunging, then lunges at <=3 px/tick',
      first is not None and first >= 8 and max(abs(d) for d in steps) <= 3, (r, xv[:30]))
r, i = solo(8); put(40, 70); b.run(0, 2)
E = S['enemies'] + 12 * i
g.mem[E + 2] = 150; g.mem[E + 3] = 72; g.mem[E + 11] = 0
xs = {}
for k in range(60):
    g.mem[E + 3] = 72; b.run(0, 1); xs.setdefault(g.b('tick'), slot(i, 2))
xv = list(xs.values()); steps = [b_ - a_ for a_, b_ in zip(xv, xv[1:])]
first = next((k for k, d in enumerate(steps) if d), None)
check('the ox paws and bellows for 8+ ticks before it charges', first is not None and first >= 8 and min(steps) <= -4, (r, xv[:24]))
r, i = solo(5); put(60, 70); b.run(0, 2)
E = S['enemies'] + 12 * i
if g.b('pface') != 2: b.run(R, 2)
g.mem[E + 2] = g.b('px') + 24; g.mem[E + 3] = g.b('py') + 4; g.mem[E + 11] = 0; x0 = slot(i, 2)
b.run(F, 2); b.run(0, 4)
check('a struck boggart is knocked back and rests', slot(i, 0) == 2 and slot(i, 2) >= x0 + 8 and slot(i, 11) > 0,
      (r, x0, slot(i, 0), slot(i, 2), slot(i, 11)))
# the swing reaches past the body-hit band, so a creature closing straight up or down can be met
r, i = solo(0); put(100, 30); b.run(0, 2)
if g.b('pface') != 2: b.run(R, 2)
E = S['enemies'] + 12 * i
g.mem[E + 2] = g.b('px') + 4; g.mem[E + 3] = g.b('py') + 50; g.poke('pinv', 0); hurt = False; swung = False
for k in range(300):
    if slot(i, 0) != 2: break
    g.mem[E + 2] = g.b('px') + 4
    if not swung and slot(i, 3) - g.b('py') < 25: b.run(F, 2); swung = True
    else: b.run(0, 1)
    hurt = hurt or g.b('p_hit')
check('a wisp rising straight at him can be cut down', slot(i, 0) != 2 and not hurt, (r, slot(i, 0), hurt, k, swung, slot(i, 2), slot(i, 3), g.b('px'), g.b('py'), g.b('demo_god')))
# --- wisps quicken at night
def wisp_speed():
    r, i = enemy_room(0)
    for k in range(3):
        if k != i: g.mem[S['enemies'] + 12 * k] = 0
    put(200, 60); b.run(0, 2)
    g.mem[S['enemies'] + 12 * i + 2] = 10; g.mem[S['enemies'] + 12 * i + 3] = 64
    t0 = g.b('tick'); b.run(0, 40); t1 = g.b('tick')
    return (slot(i, 2) - 10) / max(1, (t1 - t0) & 255)
day_v = wisp_speed(); b.cmd(0x81); b.run(0, 60); night_v = wisp_speed()
# --- night hags on the Mere
hr = next(int(r) for r, v in WJ.items() if v.get('night') == 10)
b.warp(hr); g.mem[S['enemies']] = g.mem[S['enemies'] + 12] = 0
xs = []; ys = []
for k in range(300):
    b.run(0, 1)
    if slot(2, 1) == 9 and slot(2, 0) == 2: xs.append(slot(2, 2)); ys.append(slot(2, 3) - g.b('py'))
edge = any(x <= 10 or x >= 226 for x in xs)
span = max(xs) - min(xs) if xs else 0
check('a night hag haunts the Mere by night', slot(2, 1) == 9 and len(xs) > 20, (hr, len(xs)))
check('she blinks in at an edge and crosses fast, level with him', edge and span >= 100 and all(abs(d) < 24 for d in ys[4:]), (span, ys[:8], ys[-8:], g.b('py')))
b.cmd(0x81); b.run(0, 60)
check('night hags are gone by day', not (slot(2, 1) == 9 and slot(2, 0)), (slot(2, 0), slot(2, 1)))
def try_warp(rs):
    for r in rs:
        try: b.warp(r); return r
        except RuntimeError: pass
try_warp([int(r) for r, v in WJ.items() if v.get('night') == 10]); check('no night hag spawns by day', not any(slot(i, 1) == 9 and slot(i, 0) for i in range(3)))
check('wisps drift faster by night', g.b('night') == 0 and night_v >= day_v * 1.3, (round(day_v, 2), round(night_v, 2)))
# --- boggarts throw clods
def bog_setup():
    r, i = enemy_room(5)
    for k in range(3):
        if k != i: g.mem[S['enemies'] + 12 * k] = 0
    return r, i
def pin_bog(i, x):
    put(40, 70); g.mem[S['enemies'] + 12 * i + 2] = x; g.mem[S['enemies'] + 12 * i + 3] = 74; g.mem[S['enemies'] + 12 * i + 11] = 0
r, i = bog_setup(); thrown = None; path = []
for k in range(400):
    pin_bog(i, 150); b.run(0, 1)
    if g.b('clod_on'): thrown = k; break
for k in range(60):
    if not g.b('clod_on'): break
    path.append(g.b('clod_x')); g.mem[S['enemies'] + 12 * i + 2] = 150; b.run(0, 1)
check('a boggart lobs a clod when level with Sabreman', thrown is not None, (r, thrown))
check('the clod flies at him', len(path) > 3 and path[-1] < path[0], path[:6])
# no god: a clod costs a life; the sabre bats one away
g.poke('demo_god', 0); g.poke('pinv', 0); lives = g.b('lives'); hit = False
r, i = bog_setup()
for k in range(600):
    pin_bog(i, 150); g.poke('pinv', 0); b.run(0, 1)
    if g.b('lives') < lives: hit = True; break
b.run(0, 200); check('a clod that lands costs a life', hit, (lives, g.b('lives')))
g.poke('lives', 5); r, i = solo(1); E = S['enemies'] + 12 * i; g.poke('pinv', 0); lives = g.b('lives'); died = None
for k in range(200):
    g.mem[E + 2] = g.b('px') + 4; g.mem[E + 3] = g.b('py') + 6; b.run(0, 1)
    if g.b('lives') < lives: died = [slot(j, 0) for j in range(3)]; break
check('after a death the creatures fall back to their lairs', died is not None and 2 not in died, (r, died))
g.poke('lives', 5); b.cmd(0x83)
r, i = bog_setup(); swatted = False
for k in range(600):
    pin_bog(i, 150)
    if g.b('clod_on') and abs(g.b('clod_x') - (g.b('px') + 26)) < 14 and g.b('pattack') == 0:
        b.run(R, 2); b.run(F, 2); sc = g.b('clod_on'); b.run(0, 2)
        if not g.b('clod_on'): swatted = True; break
    else: b.run(R if g.b('pface') != 2 else 0, 1)
check('the sabre bats a clod away', swatted)
# --- the Night Mare
b.warp(99); clear_en()
b.cmd(0x81); b.run(0, 60)
b.warp(52)                                       # (4,3) far from the Isle
dist = lambda: abs((g.b('mare_room') & 15) - 4) + abs((g.b('mare_room') >> 4) - 3)
d0 = dist(); b.run(0, 400); d1 = dist()
check('the Mare roams toward Sabreman at night', d1 < d0, (d0, d1))
beeps = g.beeps; arrived = False
for k in range(1500):
    b.run(0, 1)
    if g.b('mare_here'): arrived = True; break
check('hoof-beats sound as she nears', g.beeps > beeps)
check('the Mare reaches Sabreman\'s screen', arrived)
g.poke('bridle', 7); clash = False
for k in range(600):
    mx, my = g.b('mare_x'), g.b('mare_y'); px, py = g.b('px'), g.b('py')
    if not g.b('mare_here'): break
    fr = mx + 16 > px + 12; blade = px + 24 if fr else px - 8
    if abs(my - py) < 14 and mx - 4 <= blade <= mx + 36 and g.b('pattack') == 0:
        if g.b('pface') != (2 if fr else 3): b.run(R if fr else L, 1); continue
        b.run(F, 1); clash = True
    else: b.run(0, 1)
check('without the whole bridle the Mare cannot be taken', g.b('game_won') == 0)
check('she flees the screen after a clash or touch', g.b('mare_here') == 0, (clash, g.b('mare_here')))
# --- the Mare stands out on the Mere at night (own white cells, no clash)
b.warp(86); clear_en()
for k in range(3000):
    b.run(0, 1)
    if g.b('mare_here'): break
b.run(0, 6)
mx, my = g.b('mare_x'), (g.b('mare_y') + 16 + 4) & 0xF8
cells = [(my // 8 + r, mx // 8 + c) for r in range(3) for c in range(5) if mx // 8 + c < 32]
white = [rc for rc in cells if g.mem[0x5800 + rc[0] * 32 + rc[1]] & 7 == 7]
check('on the Mere the Mare has her own white cells', g.b('mare_here') and len(white) >= 8, (len(white), len(cells), g.b('mare_here'), g.b('night'), g.b('mare_room'), g.b('cur_room'), g.w('clock')))
# every white cell in her block holds only her pixels: lily ink must not remain (compare mirror)
MIR = S['mirror'] if 'mirror' in S else 0xE000
lily_left = 0
for r, c in white:
    for y in range(r * 8, r * 8 + 8):
        a = 0x4000 + ((y & 0xC0) << 5) + ((y & 7) << 8) + ((y & 0x38) << 2) + c
        if g.mem[a] & g.mem[a - 0x4000 + MIR] & ~0 and g.mem[a] == g.mem[a - 0x4000 + MIR] and g.mem[a]: lily_left += 1
check('no lily pixels share her white cells', lily_left <= 2, lily_left)
# --- bridling and the rating (every light gathered: the 100% path)
g.poke('bridle', 15); g.poke('gems', 40)
b.cmd(0x81); b.run(0, 60)
b.warp(104, near=(3, 5)); b.run(0, 10)
check('by day the Mare waits on the Isle', g.b('mare_here') == 1)
for k in range(3000):
    if g.b('game_won'): break
    mx, my = g.b('mare_x'), g.b('mare_y'); px, py = g.b('px'), g.b('py')
    fr = mx + 16 > px + 12; blade = px + 24 if fr else px - 8
    if g.b('mare_here') and abs(my - py) < 14 and mx - 4 <= blade <= mx + 36 and g.b('pattack') == 0:
        if g.b('pface') != (2 if fr else 3): b.run(R if fr else L, 1); continue
        b.run(F, 1)
    else: b.run(0, 1)
check('the whole bridle on the Isle tames the Mare', g.b('game_won') == 1)
seen = sum(1 for r in range(160) if g.mem[S['room_flags'] + r] & 2)
b.run(0, 900)
exp = seen // 4 + g.b('gems') * 3 // 4 + 4 * 5 + 10
check('rating screen percentage formula', abs(g.b('go_pct') - exp) <= 1, (g.b('go_pct'), exp, seen))
check('every room visited counts', seen == 160, seen)
check('100%: every light, screen and piece plus the Mare', g.b('go_pct') == 100, g.b('go_pct'))
for k in range(1200):
    b.run(0, 1)
    if g.b('saga_on'): break
b.run(0, 380); g.shot(os.path.join(ROOT, 'shots/h_saga_scroll.png'))
txt = sum(1 for a in range(0x5800 + 32, 0x5800 + 22 * 32) if g.mem[a] & 7)
check('100% rolls the saga-ending scroll', g.b('saga_on') >= 1 and txt > 40, (g.b('saga_on'), txt))
b.run(0, 800)
check('the scroll ends and returns', g.b('saga_on') == 2, g.b('saga_on'))
# ------------------------------------------------------------ completability (no cheats)
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/progression.py')], capture_output=True, text=True)
check('world progression: every room, item and piece reachable in order', 'COMPLETABLE' in r.stdout and r.returncode == 0, r.stdout.split('\n')[0])
# ------------------------------------------------------------ verification run
if os.path.exists(os.path.join(ROOT, 'build/miremare_demo.bin')):
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/replay_check.py')], capture_output=True, text=True)
    check('embedded demo stream replays to the ending', 'REPLAY OK' in r.stdout, r.stdout.strip().splitlines()[-1:])
print('%d/%d passed in %.0fs' % (sum(OK), len(OK), time.time() - t_start))
sys.exit(0 if all(OK) else 1)
