"""Assemble repeatedly; turn out-of-range JRs into JPs (DJNZ is reported)."""
import re, subprocess, sys
for _ in range(200):
    r = subprocess.run(['pasmo', '--alocal', 'main.asm', 'build/miremare.bin', 'build/miremare.sym'],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    m = re.search(r'ERROR on line (\d+) of file (\S+)\s*\nERROR: Relative jump out of range', out)
    if not m:
        print(out.strip() or 'ok'); break
    ln, fn = int(m.group(1)), m.group(2)
    L = open(fn).read().split('\n')
    if 'djnz' in L[ln-1]: print('djnz out of range', fn, ln); break
    L[ln-1] = re.sub(r'\bjr\b', 'jp', L[ln-1]); open(fn, 'w').write('\n'.join(L))
    print('fixed', fn, ln, L[ln-1].strip())
