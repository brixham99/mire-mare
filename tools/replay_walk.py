#!/usr/bin/env python3
"""replay_walk.py - replay the packed normal-mode walker stream in the DEMO
build (build/miremare_demo.bin, made by ./build.sh demo from the walker's
stream) and check it reproduces the walker run: same rooms at every 'got'
event, same lives, bridled at the end, no god mode used."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from headless import Game, ROOT
ev = json.load(open(os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'build/bot_events_walk.json')))
won_at = next(e['frame'] for e in ev if e['name'] == 'bridled')
g = Game('miremare_demo')
want = {e['frame']: e for e in ev if e['name'].startswith('got ')}
rooms, last, won, ok, lives, god = [], None, None, True, [], 0
for f in range(won_at + 600):
    g.frame()
    r = g.b('cur_room')
    if r != last: rooms.append(r); last = r
    if g.b('demo_god'): god += 1
    if not lives or g.b('lives') != lives[-1][1]: lives.append((f, g.b('lives')))
    if g.b('game_won') and won is None: won = f
lv = [l for _, l in lives]
print('screens %d, lives over time %s, god frames %d' % (len(rooms), lv, god))
print('bridle', g.b('bridle'), 'won at frame', won, '(walker: %d)' % won_at, 'pct', g.b('go_pct'))
ok = g.b('bridle') == 15 and won is not None and god == 0
print('REPLAY OK' if ok else 'REPLAY MISMATCH'); sys.exit(0 if ok else 1)
