#!/bin/sh
# build.sh - art -> data -> pasmo -> .tap, then the headless test suite.
#   ./build.sh            normal build + tests
#   ./build.sh notest     normal build only
#   (always also builds build/miremare_live.bin: DEMO hooks in live mode,
#    driven by tools/bot.py and tools/test_game.py)
#   ./build.sh demo       verification build (build/miremare_demo.tap) using
#                         build/demo_stream.asm (written by tools/bot.py)
set -e
cd "$(dirname "$0")"
mkdir -p build shots
[ -f tools/libz80core.so ] && [ tools/libz80core.so -nt tools/z80core.c ] || cc -O2 -shared -fPIC -o tools/libz80core.so tools/z80core.c
python3 tools/gfx.py
python3 tools/world.py
python3 tools/messages.py
python3 tools/mkscr.py
[ -f build/demo_stream.asm ] || echo '        DEFB $FE' > build/demo_stream.asm
asm() {   # $1 = DEMO flag, $2 = output stem, $3 = input stream file (DEMO)
    : > build/stream_b.asm
    if [ -n "$3" ]; then python3 tools/pack_stream.py "$3" && cp build/stream_packed_a.asm build/stream.asm && cp build/stream_packed_b.asm build/stream_b.asm
    else echo '        DEFB $FE' > build/stream.asm; fi
    echo "DEMO EQU $1" > build/cfg.asm
    echo "SFXTEST EQU ${SFXTEST:-0}" >> build/cfg.asm
    pasmo --alocal main.asm build/$2.bin build/$2.sym
    END=$(awk '/^end_all/ {print $3}' build/$2.sym | sed 's/^0*//; s/H$//')
    CODE=$(awk '/^code_end/ {print $3}' build/$2.sym | sed 's/^0*//; s/H$//')
    echo "$2: code 6000-$CODE, with buffers to $END (limit E000 = screen mirror)"
    [ $((0x$END)) -le $((0xE000)) ] || { echo "OUT OF MEMORY"; exit 1; }
}
if [ "$1" = "sfx" ]; then          # sound check: every effect in turn, 1 s apart
    SFXTEST=1 asm 0 miremare_sfx
    python3 tools/mktap.py build/miremare_sfx.bin 24576 data/loading.scr build/miremare_sfx.tap
    exit 0
fi
if [ "$1" = "demo" ]; then
    asm 1 miremare_demo build/demo_stream.asm
    python3 tools/mktap.py build/miremare_demo.bin 24576 data/loading.scr build/miremare_demo.tap
    exit 0
fi
asm 1 miremare_live      # test/bot build: live-mode cheat stream
asm 0 miremare
python3 tools/mktap.py build/miremare.bin 24576 data/loading.scr build/miremare.tap
[ "$1" = "notest" ] || python3 tools/test_game.py
