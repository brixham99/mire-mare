#!/usr/bin/env python3
"""headless.py - run Mire Mare's code in the C Z80 core with Nathan's 48K ROM
and scripted input.  Import Game for tests; screenshots via shot()."""
import ctypes, os, re
from PIL import Image
from rompath import ROM48
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
lib = ctypes.CDLL(os.path.join(HERE, 'libz80core.so'))
lib.z_mem.restype = ctypes.POINTER(ctypes.c_uint8)
lib.z_halt_t.restype = ctypes.c_long
KEYS = {'Q': (2, 0), 'W': (2, 1), 'E': (2, 2), 'R': (2, 3), 'T': (2, 4),
        '1': (3, 0), '2': (3, 1), '3': (3, 2), '4': (3, 3), '5': (3, 4),
        '0': (4, 0), '9': (4, 1), '8': (4, 2), '7': (4, 3), '6': (4, 4),
        'ENTER': (6, 0), 'SPACE': (7, 0)}
GAME = {'left': 'Q', 'right': 'W', 'up': 'R', 'down': 'E', 'fire': 'T'}

lib.z_state_size.restype = ctypes.c_int

def symbols(stem='miremare'):
    s = {}
    for line in open(os.path.join(ROOT, 'build/%s.sym' % stem)):
        m = re.match(r'(\w+)\s+EQU\s+0?([0-9A-F]+)H', line)
        if m: s[m.group(1)] = int(m.group(2), 16)
    return s

class Game:
    def __init__(self, stem='miremare', entry='start'):
        lib.z_init()
        self.mem = lib.z_mem()
        rom = open(ROM48, 'rb').read()
        ctypes.memmove(self.mem, rom, len(rom))
        self.S = symbols(stem)
        code = open(os.path.join(ROOT, 'build/%s.bin' % stem), 'rb').read()
        org = self.S['start']
        ctypes.memmove(ctypes.addressof(self.mem.contents) + org, code, len(code))
        lib.z_setpc(self.S[entry]); lib.z_setsp(org - 2)
        self.halts = []; self.beeps = 0; self.held = set()
    def frame(self, n=1):
        for _ in range(n):
            if lib.z_frame():
                raise RuntimeError('CPU error op %02X at %04X' % (lib.z_errop(), lib.z_errpc()))
            self.halts.append(lib.z_halt_t()); self.beeps += lib.z_beeps()
    def press(self, k, down=True):
        r, b = KEYS[k]; lib.z_key(r, b, 1 if down else 0)
        (self.held.add if down else self.held.discard)(k)
    def tap(self, k, n=4, after=4):
        self.press(k); self.frame(n); self.press(k, False); self.frame(after)
    def hold(self, keys, n):
        for k in keys: self.press(GAME.get(k, k))
        self.frame(n)
        for k in keys: self.press(GAME.get(k, k), False)
    def b(self, name): return self.mem[self.S[name]]
    def w(self, name): return self.mem[self.S[name]] | (self.mem[self.S[name] + 1] << 8)
    def poke(self, name, v, off=0): self.mem[self.S[name] + off] = v & 255
    def block(self, name, n, off=0):
        a = self.S[name] + off
        return bytes(self.mem[a:a + n])
    def save(self):
        buf = ctypes.create_string_buffer(lib.z_state_size()); lib.z_save(buf); return buf
    def load(self, buf): lib.z_load(buf)
    def pc(self): return lib.z_getpc()
    def pos(self): return self.b('px'), self.b('py'), self.b('cur_room')
    def shot(self, path, scale=2):
        pal = []
        for br in (0xD7, 0xFF):
            for c in range(8):
                pal.append(((c & 2) and br or 0, (c & 4) and br or 0, (c & 1) and br or 0))
        bw = 16
        img = Image.new('RGB', (256 + 2*bw, 192 + 2*bw), pal[lib.z_border() & 7])
        px = img.load()
        for y in range(192):
            base = 0x4000 | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
            for c in range(32):
                byte = self.mem[base + c]; at = self.mem[0x5800 + (y >> 3) * 32 + c]
                br = 8 if at & 64 else 0
                ink, paper = pal[(at & 7) + br], pal[((at >> 3) & 7) + br]
                for bt in range(8):
                    px[bw + c*8 + bt, bw + y] = ink if byte & (0x80 >> bt) else paper
        img.resize((img.width*scale, img.height*scale), Image.NEAREST).save(path)
