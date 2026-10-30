#!/usr/bin/env python3
"""Replay the embedded demo stream headless and check it reproduces the bot run."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from headless import Game, ROOT
g = Game('miremare_demo')
ev = json.load(open(os.path.join(ROOT, 'build/bot_events.json')))
log = []; last = None; won_frame = None; got = 0
for f in range(4000):
    g.frame()
    r = g.b('cur_room')
    if r != last: log.append((f, r)); last = r
    if g.b('game_won') and won_frame is None: won_frame = f
rooms = [r for _, r in log]
print('rooms visited in order:', rooms)
print('bridle', g.b('bridle'), 'game_won frame', won_frame, 'bot said', [e['frame'] for e in ev if e['name'] == 'bridled'])
ok = g.b('bridle') == 15 and won_frame is not None
print('REPLAY OK' if ok else 'REPLAY MISMATCH'); sys.exit(0 if ok else 1)
