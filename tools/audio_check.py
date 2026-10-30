#!/usr/bin/env python3
"""audio_check.py - objective listen-check of Fuse beeper recordings.

  audio_check.py sfx   : build/fuse_sfx.wav (the ./build.sh sfx jukebox run in
                         Fuse) -> one clip per effect in build/sfx/, plus a
                         table of duration / pitch / loudness and a check that
                         every effect is present and distinct.
  audio_check.py game  : build/fuse_demo.wav (a full game run) -> clipping,
                         clicks (lone edges in silence), DC offset left after
                         sounds, and how much of the run is sound.
Writes build/audio_report.json."""
import sys, os, json, wave
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = lambda *p: os.path.join(ROOT, 'build', *p)
NAMES = ['swing', 'hit', 'kill', 'pickup', 'quest', 'death', 'squelch', 'hoof', 'neigh',
         'ox', 'toll', 'dawn', 'hag', 'clod', 'menu', 'tune']
USE = dict(swing='sabre swing', hit='sabre hits a creature', kill='creature killed', pickup='item / lantern pickup',
           quest='bridle piece / key quest jingle', death='Sabreman dies', squelch='bog step / leech',
           hoof='Night Mare hoof-beat', neigh='Night Mare neigh', ox='bog ox bellow', toll='nightfall bells',
           dawn='dawn call', hag='night hag blinks in', clod='boggart throws a clod', menu='menu blip',
           tune='title / ending tune')

def load(path):
    w = wave.open(path); r = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.int32)
    if w.getnchannels() == 2: a = a.reshape(-1, 2)[:, 0]
    return a, r

def activity(a, r, ms=10, thr=1000):
    blk = r * ms // 1000; n = len(a) // blk
    d = np.abs(np.diff(a[:n * blk], append=a[n * blk - 1])).reshape(n, blk) if n else np.zeros((0, 1))
    return d.max(axis=1) > thr, blk

def segments(a, r, gap=0.25):
    act, blk = activity(a, r)
    segs = []; on = None; g = int(gap * 100)
    for i, x in enumerate(list(act) + [False]):
        if x and on is None: on = i
        if not x and on is not None:
            if segs and on - segs[-1][1] < g: segs[-1] = (segs[-1][0], i)
            else: segs.append((on, i))
            on = None
    return [(s * blk, e * blk) for s, e in segs]

def edges(x):
    """beeper edges in Fuse's band-limited output: crossings of the 1 ms moving mean
    that also move the signal by >2000 within the next 3 samples"""
    k = 44
    m = np.convolve(x, np.ones(k) / k, mode='same')
    s = np.sign(x - m)
    c = np.nonzero(np.diff(s) != 0)[0]
    return c

def describe(x, r):
    ms = r // 1000; n = len(x) // ms
    env = x[:n * ms].reshape(n, ms).std(axis=1)
    act = np.nonzero(env > 1000)[0]
    dur = (act[-1] - act[0] + 1) if len(act) else 0
    a0 = act[0] * ms if len(act) else 0; y = x[a0:a0 + dur * ms]
    def peakf(z):
        if len(z) < 64: return 0
        sp = np.abs(np.fft.rfft((z - z.mean()) * np.hanning(len(z))))
        return float(np.argmax(sp[1:]) + 1) * r / len(z)
    win = 5 * ms
    fs = [peakf(y[i:i + win]) for i in range(0, max(0, len(y) - win), win // 2) if y[i:i + win].std() > 1000]
    spec = np.abs(np.fft.rfft(y - y.mean() if len(y) else x, 8192))[:2048]
    return dict(duration_ms=int(dur), pitch_hz=round(peakf(y)),
                pitch_lo_hz=round(float(np.percentile(fs, 10))) if fs else 0,
                pitch_hi_hz=round(float(np.percentile(fs, 90))) if fs else 0,
                peak=int(np.abs(x).max()), clipped=int((np.abs(x) >= 32767).sum())), spec / (np.linalg.norm(spec) + 1e-9)

def write(path, x, r):
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(r)
    w.writeframes(x.astype(np.int16).tobytes()); w.close()

def sfx():
    a, r = load(B('fuse_sfx.wav'))
    segs = segments(a, r)
    # the jukebox starts 2 s after the program; drop the LOAD key clicks before it
    segs = [s for s in segs if s[0] > segs[-1][0] - 22 * r] if segs else segs
    segs = segs[-len(NAMES):]
    os.makedirs(B('sfx'), exist_ok=True)
    out = []; specs = []
    for i, ((s, e), name) in enumerate(zip(segs, NAMES)):
        x = a[s:e]; d, sp = describe(x, r); specs.append(sp)
        pre, post = a[max(0, s - r // 5):s], a[e:e + r // 5]
        d.update(name=name, use=USE[name], start_s=round(s / r, 2),
                 dc_before=int(np.median(pre)) if len(pre) else 0, dc_after=int(np.median(post)) if len(post) else 0)
        clip = a[max(0, s - r // 10):e + r // 4]
        fn = 'sfx/%02d_%s.wav' % (i + 1, name); write(B(fn), clip, r); d['clip'] = 'build/' + fn
        out.append(d)
    # distinctness: spectral similarity + duration; flag any pair that is close on both
    close = []
    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            sim = float(np.dot(specs[i], specs[j]))
            dr = abs(out[i]['duration_ms'] - out[j]['duration_ms']) / max(1, out[i]['duration_ms'], out[j]['duration_ms'])
            if sim > 0.9 and dr < 0.3: close.append((out[i]['name'], out[j]['name'], round(sim, 2), round(dr, 2)))
    allc = np.concatenate([a[max(0, s - r // 10):e + r // 4] for s, e in segs] + [np.zeros(0)])
    write(B('sfx/all_effects.wav'), a[segs[0][0] - r // 2:segs[-1][1] + r // 2] if segs else a, r)
    rep = dict(found=len(segs), expected=len(NAMES), effects=out, too_similar=close,
               clipped_samples=int((np.abs(allc) >= 32767).sum()))
    for d in out:
        print('%2s %-8s %7.1f ms  %5d Hz (%5d-%5d)  peak %5d  dc %+6d -> %+6d  %s' % (
            NAMES.index(d['name']) + 1, d['name'], d['duration_ms'], d['pitch_hz'], d['pitch_lo_hz'],
            d['pitch_hi_hz'], d['peak'], d['dc_before'], d['dc_after'], d['use']))
    print('found %d/%d effects; clipped samples %d; too similar: %s' % (len(segs), len(NAMES), rep['clipped_samples'], close or 'none'))
    return rep

def game(path=None):
    a, r = load(path or B('fuse_demo.wav'))
    act, blk = activity(a, r)
    # a click = a lone edge: a 10 ms block with exactly one or two edges and silence either side
    clicks = []
    for i in range(1, len(act) - 1):
        if act[i] and not act[i - 1] and not act[i + 1]:
            n = len(edges(a[i * blk:(i + 1) * blk])) if np.ptp(a[i * blk:(i + 1) * blk]) > 1000 else 0
            if n <= 2: clicks.append(round(i * blk / r, 2))
    segs = segments(a, r, gap=0.05)
    m = np.repeat(act, blk)[:len(a)]; a2 = a[:len(m)]
    sil = a2[~m] if len(act) else a
    rep = dict(seconds=round(len(a) / r, 1), clipped_samples=int((np.abs(a) >= 32767).sum()),
               peak=int(np.abs(a).max()), sounds=len(segs), sound_seconds=round(sum(e - s for s, e in segs) / r, 1),
               lone_clicks=len(clicks), click_times=clicks[:40], silence_dc=int(np.median(sil)) if len(sil) else 0,
               silence_noise=int(np.percentile(np.abs(sil - np.median(sil)), 99)) if len(sil) else 0)
    print(json.dumps(rep, indent=1))
    return rep

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'sfx'
    rp = B('audio_report.json')
    allr = json.load(open(rp)) if os.path.exists(rp) else {}
    allr[mode] = sfx() if mode == 'sfx' else game(sys.argv[2] if len(sys.argv) > 2 else None)
    json.dump(allr, open(rp, 'w'), indent=1)
