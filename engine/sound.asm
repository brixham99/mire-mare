; ---------------------------------------------------------------- sound.asm
; Beeper.  All effects are short blocking loops (border kept black).

; tone: D = half-period (djnz count), HL = number of half-cycles
tone:   xor a
tn_1:   xor $10
        out ($FE),a
        ld b,d
tn_2:   djnz tn_2
        ld c,a
        dec hl
        ld a,h
        or l
        ld a,c
        jr nz,tn_1
        ret

; sweep: D = start period, E = step (signed), C = steps, HL' unused; each step 6 half-cycles
sweep:  push bc
        push de
        ld hl,6
        call tone
        pop de
        ld a,d
        add a,e
        ld d,a
        pop bc
        dec c
        jr nz,sweep
        ret

; noise: E = length, C = delay mask
noise:  ld hl,start
nz_1:   ld a,(hl)
        and $10
        out ($FE),a
        inc hl
        ld a,(hl)
        and c
        inc a
        ld b,a
nz_2:   djnz nz_2
        inc hl
        dec e
        jr nz,nz_1
        xor a
        out ($FE),a
        ret

sfx_swing:
        ld d,20
        ld e,8
        ld c,8
        jp sweep
sfx_pickup:
        ld d,90
        ld e,-14
        ld c,6
        call sweep
        ld d,40
        ld hl,60
        jp tone
sfx_quest:
        ld d,120
        ld e,-10
        ld c,10
        call sweep
        ld d,120
        ld e,-10
        ld c,10
        jp sweep
sfx_kill:
        ld e,90
        ld c,$3F
        jp noise
sfx_death:
        ld d,30
        ld e,6
        ld c,36
        call sweep
        ld e,200
        ld c,$7F
        jp noise
sfx_squelch:
        ld e,12
        ld c,$FF
        jp noise
sfx_menu:
        ld d,60
        ld hl,30
        jp tone

; play_tune: HL = tune (period, halfcycles lo, hi; period 0 = rest of lo frames;
; $FF end).  Any key held stops it.
play_tune:
pt_1:   ld a,(hl)
        cp $FF
        ret z
        call any_key
        ret nz
        ld d,(hl)
        inc hl
        ld e,(hl)
        inc hl
        ld c,(hl)
        inc hl
        push hl
        ld h,c
        ld l,e
        ld a,d
        or a
        jr z,pt_rest
        call tone
        jr pt_next
pt_rest:
        ld b,l
pt_r1:  halt
        djnz pt_r1
pt_next:
        halt
        pop hl
        jr pt_1

; a struck creature: a falling "thock" (distinct from the steady menu blip)
sfx_hit:
        ld d,40
        ld e,8
        ld c,6
        jp sweep
sfx_ox: ld d,200
        ld e,4
        ld c,6
        jp sweep
; hoof-beat: a short dull knock
sfx_hoof:
        ld d,220
        ld hl,6
        call tone
        ld e,10
        ld c,$3F
        jp noise
sfx_neigh:
        ld d,30
        ld e,6
        ld c,10
        call sweep
        ld d,90
        ld e,-6
        ld c,10
        jp sweep
; nightfall: three slow bell tolls
sfx_toll:
        ld b,3
stl_1:  push bc
        ld d,180
        ld hl,90
        call tone
        ld b,8
stl_2:  halt
        djnz stl_2
        pop bc
        djnz stl_1
        ret
; dawn: a rising call
sfx_dawn:
        ld d,140
        ld e,-12
        ld c,10
        jp sweep
; night hag: a thin falling shriek as she blinks in
sfx_hag:
        ld d,12
        ld e,2
        ld c,24
        jp sweep
; boggart clod: a soft wet throw
sfx_clod:
        ld d,40
        ld e,10
        ld c,6
        call sweep
        ld e,30
        ld c,$3F
        jp noise
