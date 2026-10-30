#!/usr/bin/env python3
"""pack_stream.py - pack the demo input stream (DEFB v,n pairs + commands, as
written by tools/bot.py / walker.py into build/demo_stream.asm) so a whole
normal-mode game fits in memory.  Packed format (engine/demo.asm):
  7-byte value table, then items:
    iii nnnnn   (iii 0..6, n 1..31)  input table[iii] for n ticks
    $E0 i n     input table[i] for n ticks (n 1..255)
    $E1..$E4 args   command $80..$83 (warp 3 args, clock 0, bits 1, god 0)
    $FE         continue at $5B00 (part B, copied there at start-up)
    $FF         end: input 0 from then on
Part A goes in the code (build/stream.asm); part B (build/stream_b.asm) is
assembled after code_end and moved to $5B00-$5FFF before the font is built.
Usage: pack_stream.py [in.asm] [capacity_A]  (default capacity from build/miremare_live.sym)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = lambda p: os.path.join(ROOT, 'build', p)
NARGS = {0x80: 3, 0x81: 0, 0x82: 1, 0x83: 0}
B_CAP = 0x6000 - 0x5B00 - 1                # start-up copies len+1 bytes

def parse(path):
    vals = []
    for l in open(path):
        if 'DEFB' not in l: continue
        vals += [int(x[1:], 16) if x.startswith('$') else int(x) for x in l.split('DEFB')[1].split(';')[0].replace(' ', '').split(',')]
    items, i = [], 0
    while i < len(vals):
        v = vals[i]
        if v == 0xFF or v == 0xFE: break
        if v >= 0x80:
            n = NARGS[v]; items.append(('cmd', v, vals[i + 1:i + 1 + n])); i += 1 + n
        else:
            n = vals[i + 1]
            if items and items[-1][0] == 'in' and items[-1][1] == v: items[-1] = ('in', v, items[-1][2] + n)
            else: items.append(('in', v, n))
            i += 2
    return items

def encode(items):
    table = []
    for it in items:
        if it[0] == 'in' and it[1] not in table: table.append(it[1])
    assert len(table) <= 7, 'more than 7 distinct inputs: %r' % table
    table += [0] * (7 - len(table))
    out = []                                   # list of byte groups (never split)
    for it in items:
        if it[0] == 'cmd': out.append([0xE1 + it[1] - 0x80] + list(it[2])); continue
        k, n = table.index(it[1]), it[2]
        while n > 0:
            if n <= 31: out.append([k << 5 | n]); n = 0
            else: m = min(n, 255); out.append([0xE0, k, m]); n -= m
    return table, out

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else B('demo_stream.asm')
    if len(sys.argv) > 2: cap = int(sys.argv[2])
    else:   # part A ends at code_end; font + creature cache (3840 bytes) must end by $E000
        sym = dict(l.split()[0:3:2] for l in open(B('miremare_live.sym')) if 'EQU' in l)
        cap = 0xE000 - 3840 - int(sym['demo_data'].rstrip('H'), 16)
    items = parse(src)
    table, groups = encode(items)
    a, b = list(table), []
    for gi, g in enumerate(groups):
        if not b and len(a) + len(g) + 2 <= cap: a += g        # +2 keeps room for $FE/$FF
        else:
            if not b: a.append(0xFE)
            b += g
    (b if b else a).append(0xFF)
    assert len(a) <= cap and len(b) <= B_CAP, 'stream too big: A %d/%d B %d/%d' % (len(a), cap, len(b), B_CAP)
    w = lambda p, d: open(p, 'w').write(''.join('        DEFB %s\n' % ','.join('%d' % x for x in d[i:i + 16]) for i in range(0, len(d), 16)))
    w(B('stream_packed_a.asm'), a); w(B('stream_packed_b.asm'), b or [])
    ticks = sum(it[2] for it in items if it[0] == 'in')
    print('packed %d ticks: %d groups, part A %d/%d bytes, part B %d/%d bytes (raw %d)' % (
        ticks, len(groups), len(a), cap, len(b), B_CAP, sum(2 if it[0] == 'in' else 1 + len(it[2]) for it in items)))

if __name__ == '__main__':
    main()
