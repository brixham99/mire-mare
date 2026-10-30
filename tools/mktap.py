#!/usr/bin/env python3
"""mktap.py code.bin start screen.scr out.tap
Ultimate-style loader:
 10 BORDER 0: PAPER 0: INK 0: CLEAR start-1: LOAD ""SCREEN$ : POKE 23739,111: LOAD ""CODE : RANDOMIZE USR start
(INK 0 hides the 'Bytes:' messages, POKE 23739,111 redirects channel output so
the loading screen stays clean while the code loads.)"""
import sys, struct

def num(n):
    return str(n).encode() + bytes([0x0E, 0, 0, n & 0xFF, n >> 8, 0])

def block(flag, data):
    body = bytes([flag]) + data
    cs = 0
    for b in body: cs ^= b
    return struct.pack('<H', len(body) + 1) + body + bytes([cs])

def header(typ, name, length, p1, p2):
    return block(0x00, bytes([typ]) + name.encode()[:10].ljust(10) + struct.pack('<HHH', length, p1, p2))

code = open(sys.argv[1], 'rb').read()
start = int(sys.argv[2], 0)
scr = open(sys.argv[3], 'rb').read()
assert len(scr) == 6912
BORDER, PAPER, INK, CLEAR, LOAD, CODE, RANDOMIZE, USR, POKE, SCREEN = 0xE7, 0xDA, 0xD9, 0xFD, 0xEF, 0xAF, 0xF9, 0xC0, 0xF4, 0xAA
line = (bytes([BORDER]) + num(0) + b':' + bytes([PAPER]) + num(0) + b':' + bytes([INK]) + num(0) + b':' +
        bytes([CLEAR]) + num(start - 1) + b':' + bytes([LOAD]) + b'""' + bytes([SCREEN]) + b':' +
        bytes([POKE]) + num(23739) + b',' + num(111) + b':' +
        bytes([LOAD]) + b'""' + bytes([CODE]) + b':' + bytes([RANDOMIZE, USR]) + num(start) + b'\r')
basic = struct.pack('>H', 10) + struct.pack('<H', len(line)) + line
tap = (header(0, 'MIRE MARE', len(basic), 10, len(basic)) + block(0xFF, basic) +
       header(3, 'MIREMARE$', 6912, 16384, 32768) + block(0xFF, scr) +
       header(3, 'MIREMARE', len(code), start, 32768) + block(0xFF, code))
open(sys.argv[4], 'wb').write(tap)
print('wrote %s: BASIC %d, SCREEN$ 6912, code %d bytes at %d (ends %d)' % (sys.argv[4], len(basic), len(code), start, start + len(code)))
