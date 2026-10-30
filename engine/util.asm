; ---------------------------------------------------------------- util.asm
; rand: 16-bit xorshift (after John Metcalf) -> A (and HL)
rand:   ld hl,(seed)
        ld a,h
        rra
        ld a,l
        rra
        xor h
        ld h,a
        ld a,l
        rra
        ld a,h
        rra
        xor l
        ld l,a
        xor h
        ld h,a
        ld (seed),hl
        ret
seed:   DEFW $ACE1

; add_score: A = amount (1-9) added at digit B (0 = 100000s .. 5 = units)
add_score:
        ld hl,score
        ld e,b
        ld d,0
        add hl,de
as_1:   add a,(hl)
        cp '9'+1
        jr c,as_ok
        sub 10
        ld (hl),a
        ld a,b
        or a
        jr z,as_done
        dec hl
        dec b
        ld a,1
        jr as_1
as_ok:  ld (hl),a
as_done:
        ld a,1
        ld (hud_dirty),a
        ret

; absdiff: A = |A - B|
absdiff:
        sub b
        ret nc
        neg
        ret

; add_a_hl: HL += A
add_a_hl:
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        ret
