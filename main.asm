; ================================================================ MIRE MARE
; pasmo main.asm build/miremare.bin    (build.sh writes build/cfg.asm)
; Loaded at 24576 by the BASIC loader (CLEAR 24575).  No IX/IY used.
        INCLUDE "build/cfg.asm"
        ORG $6000
        INCLUDE "engine/defs.asm"
start:  di
        ld sp,STACK_TOP
        IF DEMO
        ld hl,code_end          ; part B of the demo stream -> $5B00 (the
        ld de,$5B00             ; font is built over it next)
        ld bc,demo_b_end-code_end+1
        ldir
        ENDIF
        xor a
        out ($FE),a
        call int_init
        call font_init
        ei
        IF SFXTEST
        jp jukebox
        ENDIF
        IF DEMO
        call wait_no_key
        jr mn_demo
        ENDIF
main_loop:
        call menu
mn_demo:
        call game_new
        call game_run
        call game_over
        jr main_loop

; dbg_gen: test harness entry - generate room (dbg_room) and stop
dbg_gen:
        di
        ld sp,STACK_TOP
        ld a,(dbg_room)
        call room_gen
dbg_end:
        jr dbg_end
dbg_room: DEFB 0

        INCLUDE "data/world.asm"
        INCLUDE "data/regions.asm"
        INCLUDE "data/tiles.asm"
        INCLUDE "data/udg.asm"
        INCLUDE "data/tune.asm"
        INCLUDE "data/sprites.asm"
        INCLUDE "engine/int.asm"
        INCLUDE "engine/screen.asm"
        INCLUDE "engine/input.asm"
        INCLUDE "engine/sound.asm"
        INCLUDE "engine/util.asm"
        INCLUDE "engine/roomgen.asm"
        INCLUDE "engine/room.asm"
        INCLUDE "engine/sprite.asm"
        INCLUDE "engine/player.asm"
        INCLUDE "engine/enemy.asm"
        INCLUDE "engine/mare.asm"
        INCLUDE "engine/clock.asm"
        INCLUDE "engine/items.asm"
        INCLUDE "engine/hud.asm"
        INCLUDE "engine/menu.asm"
        INCLUDE "engine/game.asm"
        IF DEMO
        INCLUDE "engine/demo.asm"
demo_data:
        INCLUDE "build/stream.asm"
        ENDIF
        IF SFXTEST
        INCLUDE "engine/jukebox.asm"
        ENDIF
code_end:
        IF DEMO
        INCLUDE "build/stream_b.asm"
        ENDIF
demo_b_end:
font        EQU code_end            ; 768 bytes, built at start-up
cache_mem   EQU font+768            ; 3072 bytes of pre-shifted creatures
end_all     EQU cache_mem+3072
