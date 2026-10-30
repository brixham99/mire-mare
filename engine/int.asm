; ---------------------------------------------------------------- int.asm
; IM2 frame interrupt: just counts frames.  The ROM is not used at all after
; start-up except for reading its character set (font_init).
int_init:
        ld hl,VEC_TABLE
        ld de,VEC_TABLE+1
        ld bc,256
        ld (hl),$FD
        ldir
        ld a,$C3
        ld (ISR_JP),a
        ld hl,isr
        ld (ISR_JP+1),hl
        ld a,VEC_TABLE/256
        ld i,a
        im 2
        ret

isr:    push af
        ld a,(frames)
        inc a
        ld (frames),a
        pop af
        ei
        reti

; wait_tick: game runs at 25 Hz.  Always syncs to an interrupt, and waits
; until at least 2 frames have passed since the last tick.
wait_tick:
        halt
wt_1:   ld a,(frames)
        ld hl,last_tick
        sub (hl)
        cp 2
        jr nc,wt_2
        halt
        jr wt_1
wt_2:   ld a,(frames)
        ld (last_tick),a
        ret

frames:     DEFB 0
last_tick:  DEFB 0
