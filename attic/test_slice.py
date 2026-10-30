#!/usr/bin/env python3
"""Scripted, assertion-based test of the Mire Mare slice in the headless core."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import Game
OK = []
def check(name, cond, info=''):
    print(('PASS ' if cond else 'FAIL ') + name + (' ' + str(info) if info else ''))
    OK.append(cond)

g = Game(); S = g.S
def poke(n, v, off=0): g.mem[S[n] + off] = v
def put(x, y): poke('px', x); poke('py', y)
def no_enemies():
    for i in range(3): g.mem[S['enemies'] + i*10] = 0

g.frame(120); g.press("SPACE"); g.frame(40); g.press("SPACE", False); g.frame(10)
check('menu tune beeps', g.beeps > 0, g.beeps)
g.tap('2'); check('select kempston', g.b('ctrl_type') == 1)
g.tap('1'); check('select keyboard', g.b('ctrl_type') == 0)
g.tap('0'); g.frame(10)
check('game started in start room', g.pos() == (128, 48, 5), g.pos())
check('5 lives', g.b('lives') == 5)
no_enemies()
# --- walking
x0 = g.b('px'); g.hold(['right'], 20); check('walk right 2px/tick', g.b('px') - x0 == 20, g.b('px') - x0)
y0 = g.b('py'); g.hold(['up'], 10); check('walk up', g.b('py') < y0, (y0, g.b('py')))
check('facing up uses pdir 1', g.b('pdir') == 1)
# --- solid scenery: fern block room F tiles (4..5, 3..4) -> push into it from the right
put(104, 50); g.hold(['left'], 20); check('blocked by ferns', g.b('px') >= 90, g.b('px'))
# --- shallow mire slows
put(56, 110); g.frame(4); x0 = g.b('px'); g.hold(['right'], 20)
check('shallow mire halves speed', 8 <= g.b('px') - x0 <= 12, g.b('px') - x0)
# --- flip screen left: F -> E
put(0, 66); g.hold(['left'], 6); check('flip left to room E', g.pos()[2] == 4 and g.b('px') == 232, g.pos())
g.shot('shots/h_roomE.png')
no_enemies()
# --- gem pickup in room E (tile col 11,row 5)
put(172, 66); g.frame(4)
check('gem collected', g.b('gems') == 1, g.b('gems'))
check('score 500', bytes(g.mem[S['score'] + i] for i in range(6)) == b'000500')
# leave and come back: gem stays collected
put(232, 66); g.hold(['right'], 6); check('flip right back to F', g.pos()[2] == 5, g.pos())
put(0, 66); g.hold(['left'], 6); no_enemies()
rb = S['roombuf']; check('collected gem not respawned', g.mem[rb + 5*16 + 11] == 0, g.mem[rb + 5*16 + 11])
# --- bog sinking and drowning (room E, bog at row 5 col 5)
poke('pinv', 0); put(76, 66); g.frame(30)
s1 = g.b('psink'); check('sinking in bog', s1 > 0, s1)
g.shot('shots/h_sinking.png')
g.frame(200); check('drowned -> life lost', g.b('lives') == 4, g.b('lives'))
check('respawn at entry', (g.b('px'), g.b('py')) == (g.b('entry_x'), g.b('entry_y')), (g.b('px'), g.b('py')))
# --- sabre kills an enemy: place a toad right of the player
g.frame(60); poke('pinv', 0); put(100, 100)
e = S['enemies']
for k, v in enumerate([2, 1, 124, 100, 0, 0, 0, 0, 124, 100]): g.mem[e + k] = v
g.hold(['right'], 2); put(100, 100)
g.tap('T', 2, 2); g.frame(2)
check('sabre kills toad', g.mem[e] in (3, 4), g.mem[e])
check('kill score', bytes(g.mem[S['score'] + i] for i in range(6)) == b'000600', bytes(g.mem[S['score']+i] for i in range(6)))
g.frame(20); check('dead toad waits', g.mem[e] == 4, g.mem[e])
# --- touching an enemy costs a life
poke('pinv', 0); lv = g.b('lives')
for k, v in enumerate([2, 2, 104, 104, 2, 0, 0, 0, 104, 104]): g.mem[e + k] = v
g.frame(30); check('enemy touch -> life lost', g.b('lives') == lv - 1, (lv, g.b('lives')))
check('invulnerable after respawn', g.b('pinv') > 0)
# --- bridle piece in room D (index 3, tile col 13,row 1): enter from C via the right edge
g.frame(60); no_enemies()
g.mem[S['cur_room']] = 2; put(232, 64)
g.hold(['right'], 6)
check('flip right to room D', g.pos()[2] == 3, g.pos())
no_enemies(); put(200, 2); g.frame(6)
check('bridle bit collected', g.b('bridle') & 1 == 1, g.b('bridle'))
g.frame(10); g.shot('shots/h_rhyme.png'); g.frame(220)
# --- timing: worst first-HALT T-state over gameplay frames
gameplay = g.halts[300:]
check('every tick fits in 2 frames', max(gameplay) < 2 * 69888, max(gameplay))
print('worst CPU per frame (T):', max(gameplay))
# --- game over
g.mem[S['lives']] = 1; poke('pinv', 0); g.mem[S['cur_room']] = 5
put(0, 66); g.hold(['left'], 4); no_enemies(); put(76, 66)
g.frame(300); g.shot('shots/h_gameover.png')
check('game over reached', g.b('lives') == 0)
g.frame(700); g.tap('T', 4, 60); g.frame(200)
g.shot('shots/h_menu_again.png')
check('back at menu', g.mem[0x5800+3*32+8] == 0x44)
# --- Kempston joystick
g.frame(30); g.press('SPACE'); g.frame(40); g.press('SPACE', False); g.frame(10)
g.tap('2', 4, 6); check('select kempston (2nd game)', g.b('ctrl_type') == 1)
g.tap('0'); g.frame(10)
from headless import lib
x0 = g.b('px'); lib.z_kempston(1); g.frame(20); lib.z_kempston(0)
check('kempston right moves', g.b('px') - x0 == 20, g.b('px') - x0)
print('%d/%d passed' % (sum(OK), len(OK)))
sys.exit(0 if all(OK) else 1)
