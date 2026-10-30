"""Drive Fuse (SDL) on a private Xvfb: load file, press keys, grab window screenshots."""
import subprocess, time, os, sys, re
DISP=':55'; ENV=dict(os.environ, DISPLAY=DISP, SDL_AUDIODRIVER='dummy')
def ensure_x():
    # start the private Xvfb if it is not up (e.g. after a box restart)
    if subprocess.run(['xdotool','getmouselocation'],env=ENV,capture_output=True).returncode:
        subprocess.Popen(['Xvfb',DISP,'-screen','0','800x600x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(1.5)
class Fuse:
    def __init__(self, f, extra=(), sound=False):
        ensure_x(); subprocess.run(['pkill','-x','fuse-sdl']); time.sleep(0.5)
        env=ENV
        if sound:
            env=dict(ENV, SDL_AUDIODRIVER='disk', SDL_DISKAUDIOFILE=sound if isinstance(sound,str) else '/dev/null')
        self.p=subprocess.Popen(['fuse-sdl','--machine','48','--sound' if sound else '--no-sound','--graphics-filter','normal',
            '--no-confirm-actions','--kempston','--no-statusbar', *extra, f], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            time.sleep(0.2)
            r=subprocess.run(['xdotool','search','--pid',str(self.p.pid)],env=ENV,capture_output=True,text=True).stdout.split()
            if r: self.win=r[-1]; break
        time.sleep(1)
        g=subprocess.run(['xdotool','getwindowgeometry','--shell',self.win],env=ENV,capture_output=True,text=True).stdout
        g=dict(l.split('=') for l in g.split())
        self.x,self.y,self.w,self.h=int(g['X']),int(g['Y']),int(g['WIDTH']),int(g['HEIGHT'])
        subprocess.run(['xdotool','windowfocus','--sync',self.win],env=ENV,capture_output=True)
        subprocess.run(['xdotool','mousemove','0','0'],env=ENV,capture_output=True)
    def shot(self, out):
        subprocess.run(['ffmpeg','-loglevel','error','-y','-f','x11grab','-video_size',f'{self.w}x{self.h}',
            '-i',f'{DISP}+{self.x},{self.y}','-frames:v','1','-vf','scale=iw*2:ih*2:flags=neighbor',out],env=ENV)
    def key(self, k, hold=0.15):
        subprocess.run(['xdotool','keydown',k],env=ENV); time.sleep(hold)
        subprocess.run(['xdotool','keyup',k],env=ENV)
    def hold(self, keys, secs):
        for k in keys: subprocess.run(['xdotool','keydown',k],env=ENV)
        time.sleep(secs)
        for k in keys: subprocess.run(['xdotool','keyup',k],env=ENV)
    def close(self): self.p.terminate()
