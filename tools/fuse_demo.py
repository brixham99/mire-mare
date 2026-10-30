#!/usr/bin/env python3
"""fuse_demo.py - load build/miremare_demo.tap in Fuse on the real 48K ROM
(LOAD "" typed on the ROM), with sound on, recording a Fuse movie (.fmf:
every emulated frame + beeper audio).  The DEMO build replays the bot's
recorded input stream, so this is the full verification run on real Fuse.
Then fmfconv -> build/fuse_demo.mp4 (video+audio) and build/fuse_demo.wav."""
import sys, os, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fusectl import Fuse, ENV
from rompath import ROM48
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 110
stem = sys.argv[2] if len(sys.argv) > 2 else 'demo'   # 'sfx' records the sound-check build
shots = stem == 'demo'
fmf = os.path.join(ROOT, 'build/fuse_%s.fmf' % stem)
if os.path.exists(fmf): os.remove(fmf)
f = Fuse(os.path.join(ROOT, 'build/miremare_%s.tap' % stem),
         ['--rom-48', ROM48, '--traps', '--no-fastload', '--no-auto-load',
          '--movie-start', fmf], sound=os.path.join(ROOT, 'build/fuse_%s_audio.raw' % stem))
xd0 = lambda *a: subprocess.run(['xdotool', *a], env=ENV)
time.sleep(3); f.key('j'); time.sleep(.3)
for _ in range(2):
    xd0('keydown', 'Control_L'); f.key('p'); xd0('keyup', 'Control_L'); time.sleep(.3)
f.key('Return'); time.sleep(1); f.key('F8')
t0 = time.time()
n = 0
while time.time() - t0 < secs:
    time.sleep(5); n += 1
    if shots: f.shot(os.path.join(ROOT, 'build/fuse_live_%03d.png' % n))
f.close(); time.sleep(2)
print('fmf', os.path.getsize(fmf))
