; ---------------------------------------------------------------- clock.asm
; Day (4 min) and night (2 min).  Night dims the fen (BRIGHT off), raises
; the bog (shallow mire becomes deep), opens night lilies and spirit doors
; (with the lantern), raises bog-bodies and lets the Night Mare roam.
clock_init:
        xor a
        ld (night),a
        ld (days),a
        ld hl,DAY_LEN
        ld (clock),hl
        jp set_light

set_light:
        ld a,(night)
        or a
        ld a,$FF
        ld b,$47
        jr z,sl_1
        ld a,$BF
        ld b,$07
sl_1:   ld (dim_mask),a
        ld a,b
        ld (floor_attr),a
        ret

clock_tick:
        ld hl,(clock)
        dec hl
        ld (clock),hl
        ld a,h
        or l
        ret nz
        ld a,(night)
        xor 1
        ld (night),a
        ld hl,NIGHT_LEN
        jr nz,ct_1
        ld hl,days
        inc (hl)
        ld hl,DAY_LEN
ct_1:   ld (clock),hl
        call set_light
        ld a,(night)
        or a
        jr nz,ct_2
        ld a,ISLE_HOME          ; dawn: the Mare is back on her isle
        ld (mare_room),a
        xor a
        ld (mare_cool),a
        call sfx_dawn
        jr ct_3
ct_2:   call sfx_toll
ct_3:   call erase_all
        ld a,(cur_room)
        call room_load
        call rescue
        ld a,1
        ld (room_changed),a
        jp hud_clock

; rescue: if Sabreman now stands in something solid (a lily closed at dawn),
; move him to the nearest walkable tile.
rescue: ld a,(px)
        ld b,a
        ld a,(py)
        ld c,a
        call feet_free
        ret z
        ld a,$FF
        ld (rs_best),a
        ld c,1
rs_y:   ld b,1
rs_x:   push bc
        call cell_hl
        ld a,(hl)
        ld hl,tile_flags
        call add_a_hl
        ld a,(hl)
        and F_SOLID|F_SINK
        jr nz,rs_n
        ; candidate position -> feet box clear?
        ld a,b
        add a,a
        add a,a
        add a,a
        add a,a
        sub 4
        ld d,a
        ld a,c
        add a,a
        add a,a
        add a,a
        add a,a
        sub 12
        ld e,a
        push de
        ld b,d
        ld c,e
        call feet_free
        pop de
        jr nz,rs_n
        ; distance
        ld a,(px)
        ld b,d
        call absdiff
        ld h,a
        ld a,(py)
        ld b,e
        call absdiff
        srl a
        srl h
        add a,h
        ld hl,rs_best
        cp (hl)
        jr nc,rs_n
        ld (hl),a
        ld (rs_x0),de
rs_n:   pop bc
        inc b
        ld a,b
        cp 15
        jr nz,rs_x
        inc c
        ld a,c
        cp 10
        jr nz,rs_y
        ld a,(rs_best)
        cp $FF
        jr nz,rs_ok
        ld a,150                ; nowhere dry: a grace of water-walking
        ld (pu_water),a
        ret
rs_ok:  ld de,(rs_x0)
        ld a,d
        ld (px),a
        ld (entry_x),a
        ld a,e
        ld (py),a
        ld (entry_y),a
        ret
rs_best: DEFB 0
rs_x0:   DEFW 0

; hud_clock: sun or moon at row 0 col 20
hud_clock:
        xor a
        ld (pr_row),a
        ld a,20
        ld (pr_col),a
        ld a,(night)
        or a
        ld a,$46
        ld b,CH_SUN
        jr z,hc_1
        ld a,$45
        ld b,CH_MOON
hc_1:   ld (pr_attr),a
        ld a,b
        jp print_char

clock:  DEFW 0
night:  DEFB 0
days:   DEFB 0
