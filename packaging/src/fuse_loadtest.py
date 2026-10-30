"""Real-ROM, real-speed tape load of build/miremare.tap in Fuse (roms/48.rom), typing LOAD "" as a user would; screenshots."""
import sys, time, os, subprocess
sys.path.insert(0, 'tools'); from fusectl import Fuse, ENV
from rompath import ROM48 as ROM
f = Fuse('build/miremare.tap', extra=('--rom-48', ROM, '--no-traps', '--no-fastload', '--no-accelerate-loader', '--no-auto-load', '--detect-loader'))
time.sleep(3)
f.key('j')                                   # LOAD keyword
for _ in range(2):
    subprocess.run(['xdotool', 'keydown', 'ctrl'], env=ENV); f.key('p', hold=.2); subprocess.run(['xdotool', 'keyup', 'ctrl'], env=ENV); time.sleep(.5)   # SYMBOL SHIFT+P = "
time.sleep(.3); f.shot('packaging/out/06_fuse_load_0_typed.png')
f.key('Return'); t0 = time.time()
for t, name in ((12, 'a_screen_loading'), (22, 'b_screen_loaded'), (120, 'c_code_loading')):
    time.sleep(max(0, t - (time.time() - t0))); f.shot(f'packaging/out/06_fuse_load_{name}.png')
time.sleep(max(0, 240 - (time.time() - t0))); f.shot('packaging/out/06_fuse_load_d_after_load.png')
f.close(); print('done', time.time() - t0)
