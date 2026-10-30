#!/bin/sh
# balance_runs.sh - normal-mode (no god) walker runs at several skill levels:
# look-ahead horizon 12/8/6 ticks (0.48/0.32/0.24 s of foresight) and a
# reflex-only bot.  Logs: build/walk_log_h12.json ... build/walk_log_reflex.json
cd "$(dirname "$0")/.."
for H in ${HS:-12 8 6}; do python3 tools/walker.py --horizon $H --tag h$H > build/walk_h$H.txt 2>&1; done
python3 tools/walker.py --reflex-only --tag reflex > build/walk_reflex.txt 2>&1
python3 - <<'PY'
import json
for t in ('h12', 'h8', 'h6', 'reflex'):
    d = json.load(open('build/walk_log_%s.json' % t))
    print('%-6s won=%-5s deaths=%d lives_left=%d game %.1f min  deaths: %s' % (t, d['won'], len(d['deaths']), d['lives_left'], d['minutes'],
          '; '.join('%s r%d %s%s' % (x['cause'], x['room'], x['region'], ' (night)' if x['night'] else '') for x in d['deaths'])))
PY
