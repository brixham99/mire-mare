"""Generate all 160 rooms once with the real Z80 generator and cache them
(build/rooms_gen.json) for the bot and tests."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from headless import ROOT

def load():
    p = os.path.join(ROOT, 'build/rooms_gen.json')
    binp = os.path.join(ROOT, 'build/miremare.bin')
    if os.path.exists(p) and os.path.getmtime(p) > os.path.getmtime(binp):
        return {int(k): v for k, v in json.load(open(p)).items()}
    from validate_world import Gen
    g = Gen(); out = {}
    for r in range(160):
        out[r] = g.run(r)
    out_flags = list(g.flags)
    json.dump({str(k): v for k, v in out.items()}, open(p, 'w'))
    json.dump(out_flags, open(os.path.join(ROOT, 'build/tile_flags.json'), 'w'))
    return out

def flags():
    load()
    return json.load(open(os.path.join(ROOT, 'build/tile_flags.json')))
