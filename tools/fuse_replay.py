#!/usr/bin/env python3
"""fuse_replay.py - load the .tap in Fuse (Nathan's 48K ROM), start a game and
replay the autopilot key timeline through xdotool in real time while ffmpeg
records the window.  Output: build/fuse_session.mp4 + build/fuse_replay.json"""
import sys, os, time, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fusectl import Fuse, ENV
from rompath import ROM48
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tl = json.load(open(os.path.join(ROOT, 'build/demo_timeline.json')))
f = Fuse(os.path.join(ROOT, 'build/miremare.tap'), ['--rom-48', ROM48, '--traps', '--fastload', '--no-auto-load'])
xd0 = lambda *a: subprocess.run(['xdotool', *a], env=ENV)
time.sleep(3); f.key('j'); time.sleep(.3)
for _ in range(2):                               # LOAD "" typed on the real ROM
    xd0('keydown', 'Control_L'); f.key('p'); xd0('keyup', 'Control_L'); time.sleep(.3)
f.key('Return'); time.sleep(1); f.key('F8')
time.sleep(10)
f.shot(os.path.join(ROOT, 'shots/fuse_04_menu_autoload.png'))
xd = lambda *a: subprocess.run(['xdotool', *a], env=ENV)
xd('keydown', 'space'); time.sleep(0.8); xd('keyup', 'space'); time.sleep(0.4)
xd('keydown', '1'); time.sleep(0.1); xd('keyup', '1'); time.sleep(0.4)
out = os.path.join(ROOT, 'build/fuse_session.mp4')
rec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'x11grab', '-framerate', '50',
                        '-video_size', f'{f.w}x{f.h}', '-i', f'{ENV["DISPLAY"]}+{f.x},{f.y}',
                        '-t', str(tl['frames'] / 50 + 6), '-c:v', 'libx264', '-preset', 'ultrafast', '-qp', '0', out], env=ENV)
time.sleep(1.5)
t_rec = time.perf_counter() - 1.5
KM = {'Q': 'q', 'W': 'w', 'E': 'e', 'R': 'r', 'T': 't', '0': '0', '1': '1'}
held = set(); t0 = time.perf_counter()
for frame, keys in tl['timeline']:
    while time.perf_counter() < t0 + frame / 50: time.sleep(0.001)
    want = set(keys)
    for k in held - want: xd('keyup', KM[k])
    for k in want - held: xd('keydown', KM[k])
    held = want
for k in held: xd('keyup', KM[k])
json.dump({'game_start_in_video_s': t0 - t_rec, 'frames': tl['frames']}, open(os.path.join(ROOT, 'build/fuse_replay.json'), 'w'))
rec.wait(); time.sleep(1); f.shot(os.path.join(ROOT, 'shots/fuse_09_end.png')); f.close()
print('recorded', out, 'game start at %.2fs' % (t0 - t_rec))
