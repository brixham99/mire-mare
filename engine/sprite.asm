; ---------------------------------------------------------------- sprite.asm
; Masked, pre-shifted sprites drawn straight to the screen; erased by copying
; the clean mirror back.  A draw record (9 bytes) remembers what to erase:
;   +0 drawn flag, +1/2 screen addr, +3 width bytes, +4 rows,
;   +5/6 attr addr, +7 attr width (0 = none), +8 attr rows
; Colour rule: paper is always black.  The player takes the ink of whatever
; cell it stands in (white on floor); enemies paint their own ink, but only
; on empty-floor cells.  So no cell ever holds more than 2 colours.

; frame_gfx: HL = SPR_xxx table (4 DW, one per 2-px shift), E = x -> HL = data
frame_gfx:
        ld a,e
        and 6
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ret

; draw_spr: D = screen y, E = x (pixels), HL = shifted data, B = rows,
; C = width bytes; (ds_rec) = record to fill.
draw_spr:
        ld (ds_gfx),hl
        ld a,e
        rrca
        rrca
        rrca
        and $1F
        ld e,a
        call scr_addr
        push hl
        ld hl,(ds_rec)
        ld (hl),1
        inc hl
        pop de
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld (hl),c
        inc hl
        ld (hl),b
        inc hl
        inc hl
        inc hl
        ld (hl),0               ; no attr rect unless color_spr sets one
        ex de,hl
        ld de,(ds_gfx)
ds_row: push bc
        push hl
        ld b,c
ds_b:   ld a,(de)               ; mask
        inc de
        and (hl)
        ld c,a
        ld a,(de)               ; ink
        inc de
        or c
        ld (hl),a
        inc l
        djnz ds_b
        pop hl
        call down_hl
        pop bc
        djnz ds_row
        ret

; color_spr: D = screen y, E = x of a 16x16 sprite, A = attr.  Paints floor
; cells under it and records the rect in (ds_rec).
color_spr:
        ld (cs_attr),a
        ld a,(cs_h)
        dec a
        add a,d
        rrca
        rrca
        rrca
        and $1F
        ld b,a
        ld a,d
        rrca
        rrca
        rrca
        and $1F
        ld d,a
        ld a,b
        sub d
        inc a
        ld b,a                  ; rows
        ld a,(cs_w)
        dec a
        add a,e
        rrca
        rrca
        rrca
        and $1F
        ld c,a
        ld a,e
        rrca
        rrca
        rrca
        and $1F
        ld e,a
        ld a,c
        sub e
        inc a
        ld c,a                  ; cols
        call attr_addr
        push hl
        ld hl,(ds_rec)
        ld de,5
        add hl,de
        pop de
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld (hl),c
        inc hl
        ld (hl),b
        ex de,hl
cs_r:   push bc
        push hl
        ld b,c
cs_c:   ld a,h
        add a,MOFS
        ld d,a
        ld e,l
        ld a,(floor_attr)
        ex de,hl
        cp (hl)
        ex de,hl
        jr nz,cs_n
        ld a,(cs_attr)
        ld (hl),a
cs_n:   inc l
        djnz cs_c
        pop hl
        ld de,32
        add hl,de
        pop bc
        djnz cs_r
        ret

; erase_rec: HL = record.  Restores bitmap (and attrs) from the mirror.
erase_rec:
        ld a,(hl)
        or a
        ret z
        ld (hl),0
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld b,(hl)
        inc hl
        push hl
        ex de,hl
er_row: push bc
        push hl
        ld a,h
        add a,MOFS
        ld d,a
        ld e,l
        ld b,c
er_b:   ld a,(de)
        ld (hl),a
        inc e
        inc l
        djnz er_b
        pop hl
        call down_hl
        pop bc
        djnz er_row
        pop hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld a,c
        or a
        ret z
        ex de,hl
er_ar:  push bc
        push hl
        ld a,h
        add a,MOFS
        ld d,a
        ld e,l
        ld b,c
er_ab:  ld a,(de)
        ld (hl),a
        inc e
        inc l
        djnz er_ab
        pop hl
        ld bc,32
        add hl,bc
        pop bc
        djnz er_ar
        ret

erase_all:
        ld hl,rec_mare
        call erase_rec
        ld hl,rec_player
        call erase_rec
        ld hl,rec_en
        call erase_rec
        ld hl,rec_en+9
        call erase_rec
        ld hl,rec_en+18
        call erase_rec
        ld hl,rec_clod
        jp erase_rec

ds_gfx:     DEFW 0
ds_rec:     DEFW 0
cs_attr:    DEFB 0
cs_w:       DEFB 16
cs_h:       DEFB 16
floor_attr: DEFB $47
rec_mare:   DEFS 9
rec_player: DEFS 9
rec_en:     DEFS 27
rec_clod:   DEFS 9

; ---------------------------------------------------------------- runtime shifting
; Creature graphics are stored unshifted (rows x W bytes x (mask,data)).
; rt_row shifts one row by (rt_sh) pixels into rt_buf (W+1 pairs): right
; shifts for 0-4, left shifts (with a one-byte offset) for 5-7.
; rt_setup: C = W (bytes)
rt_setup:
        ld a,c
        ld (rt_w),a
        inc a
        ld (rt_w1),a
        add a,a
        ld (rt_w2b),a
        ld a,c
        add a,a
        ld (rt_w2),a
        ld hl,rt_buf
        call add_a_hl
        ld (rt_last),hl
        ret

; rt_row: DE = source row -> rt_buf; DE advanced past the row.
rt_row: ld a,(rt_sh)
        cp 5
        jr nc,rr_l
        ex de,hl
        ld de,rt_buf
        ld bc,(rt_w2)
        ld b,0
        ldir
        ex de,hl
        ld (hl),$FF
        inc hl
        ld (hl),0
        ld a,(rt_sh)
        or a
        ret z
        ld c,a
rr_r1:  ld hl,rt_buf
        ld a,(rt_w1)
        ld b,a
        scf
rr_r2:  rr (hl)
        inc hl
        inc hl
        djnz rr_r2
        ld hl,rt_buf+1
        ld a,(rt_w1)
        ld b,a
        or a
rr_r3:  rr (hl)
        inc hl
        inc hl
        djnz rr_r3
        dec c
        jr nz,rr_r1
        ret
rr_l:   ld hl,rt_buf
        ld (hl),$FF
        inc hl
        ld (hl),0
        inc hl
        ex de,hl
        ld bc,(rt_w2)
        ld b,0
        ldir
        ex de,hl
        ld a,(rt_sh)
        neg
        add a,8
        ld c,a
rr_l1:  ld hl,(rt_last)
        ld a,(rt_w1)
        ld b,a
        scf
rr_l2:  rl (hl)
        dec hl
        dec hl
        djnz rr_l2
        ld hl,(rt_last)
        inc hl
        ld a,(rt_w1)
        ld b,a
        or a
rr_l3:  rl (hl)
        dec hl
        dec hl
        djnz rr_l3
        dec c
        jr nz,rr_l1
        ret

; fill_rec: HL = screen address, B = rows, C = width bytes -> (ds_rec)
fill_rec:
        push hl
        ex de,hl
        ld hl,(ds_rec)
        ld (hl),1
        inc hl
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld (hl),c
        inc hl
        ld (hl),b
        inc hl
        inc hl
        inc hl
        ld (hl),0
        pop hl
        ret

; draw_rt: D = screen y, E = x, HL = unshifted data, B = rows, C = W bytes.
; Shifts as it draws (used for the Night Mare).
draw_rt:
        push hl
        push bc
        call rt_setup
        ld a,e
        and 7
        ld (rt_sh),a
        ld a,e
        rrca
        rrca
        rrca
        and $1F
        ld e,a
        call scr_addr
        ld (rt_scr),hl
        pop bc
        push bc
        inc c
        call fill_rec
        pop bc
        pop de
drt_r:  push bc
        call rt_row
        push de
        ld hl,(rt_scr)
        ld de,rt_buf
        ld a,(rt_w1)
        ld b,a
drt_b:  ld a,(de)
        inc de
        and (hl)
        ld c,a
        ld a,(de)
        inc de
        or c
        ld (hl),a
        inc l
        djnz drt_b
        ld hl,(rt_scr)
        call down_hl
        ld (rt_scr),hl
        pop de
        pop bc
        djnz drt_r
        ret

; cache_build: pre-shift (4 shifts x 2 frames) every creature type present
; in the room into cache_mem, so drawing is as fast as the player's.
cache_build:
        ld hl,ctype_ptr
        ld b,20
        xor a
cbl_0:  ld (hl),a
        inc hl
        djnz cbl_0
        ld hl,cache_mem
        ld (cache_free),hl
        ld hl,enemies
        ld b,3
cbl_1:  push bc
        push hl
        ld a,(hl)
        or a
        jr z,cbl_n
        inc hl
        ld a,(hl)
        call cache_type
cbl_n:  pop hl
        ld de,ESLOT
        add hl,de
        pop bc
        djnz cbl_1
        ret
cache_type:
        ld (ct_t),a
        add a,a
        ld hl,ctype_ptr
        call add_a_hl
        ld a,(hl)
        inc hl
        or (hl)
        ret nz
        dec hl
        ld de,(cache_free)
        ld (hl),e
        inc hl
        ld (hl),d
        ld a,(ct_t)
        call etype_ptr
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (ct_fa),de
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (ct_fb),de
        ld c,(hl)
        inc hl
        ld a,(hl)
        ld (ct_rows),a
        call rt_setup
        ld hl,(ct_fa)
        call ct_frame
        ld hl,(ct_fb)
ct_frame:
        ld (ct_src),hl
        xor a
ctf_1:  ld (rt_sh),a
        ld de,(ct_src)
        ld a,(ct_rows)
        ld b,a
ctf_2:  push bc
        call rt_row
        push de
        ld hl,rt_buf
        ld de,(cache_free)
        ld a,(rt_w2b)
        ld c,a
        ld b,0
        ldir
        ld (cache_free),de
        pop de
        pop bc
        djnz ctf_2
        ld a,(rt_sh)
        add a,2
        cp 8
        jr nz,ctf_1
        ret

rt_sh:      DEFB 0
rt_w:       DEFB 0
rt_w1:      DEFB 0
rt_w2:      DEFW 0
rt_w2b:     DEFB 0
rt_last:    DEFW 0
rt_scr:     DEFW 0
rt_buf:     DEFS 10
ct_t:       DEFB 0
ct_fa:      DEFW 0
ct_fb:      DEFW 0
ct_rows:    DEFB 0
ct_src:     DEFW 0
cache_free: DEFW 0
ctype_ptr:  DEFS 20
