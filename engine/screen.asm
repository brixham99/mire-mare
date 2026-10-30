; ---------------------------------------------------------------- screen.asm
; Screen addressing, clearing and text output.

; cls_all: clear bitmap, set every attribute to A
cls_all:
        push af
        ld hl,$4000
        ld de,$4001
        ld bc,6143
        ld (hl),0
        ldir
        pop af
        ld hl,$5800
        ld de,$5801
        ld bc,767
        ld (hl),a
        ldir
        ret

; scr_addr: D = pixel y (0-191), E = byte column (0-31) -> HL. Corrupts A.
scr_addr:
        ld a,d
        and $C0
        rra
        rra
        rra
        or $40
        ld h,a
        ld a,d
        and 7
        or h
        ld h,a
        ld a,d
        rla
        rla
        and $E0
        or e
        ld l,a
        ret

; down_hl: HL one pixel row down. Corrupts A.
down_hl:
        inc h
        ld a,h
        and 7
        ret nz
        ld a,l
        add a,32
        ld l,a
        ret c
        ld a,h
        sub 8
        ld h,a
        ret

; char_addr: D = char row (0-23), E = col -> HL (top pixel line). Corrupts A.
char_addr:
        ld a,d
        and $18
        or $40
        ld h,a
        ld a,d
        and 7
        rrca
        rrca
        rrca
        or e
        ld l,a
        ret

; attr_addr: D = char row, E = col -> HL. Corrupts A.
attr_addr:
        ld a,d
        rrca
        rrca
        rrca
        ld l,a
        and 3
        or $58
        ld h,a
        ld a,l
        and $E0
        or e
        ld l,a
        ret

; font_init: build a bold 8x8 font from the ROM character set (Ultimate-style
; chunky lettering stand-in until the custom font is drawn).
font_init:
        ld hl,$3D00
        ld de,font
        ld bc,768
fi_1:   ld a,(hl)
        srl a
        or (hl)
        ld (de),a
        inc hl
        inc de
        dec bc
        ld a,b
        or c
        jr nz,fi_1
        ret

; glyph_ptr: A = char -> HL = 8 bytes of glyph.  128+ = UDGs.
glyph_ptr:
        cp 128
        jr c,gp_font
        sub 128
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld bc,UDG_life
        add hl,bc
        ret
gp_font:
        sub 32
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld bc,font
        add hl,bc
        ret

; print_char: A = char at (pr_row,pr_col) in pr_attr; advances pr_col.
print_char:
        push hl
        push de
        push bc
        push af
        ld a,(pr_row)
        ld d,a
        ld a,(pr_col)
        ld e,a
        call attr_addr
        ld a,(pr_attr)
        ld (hl),a
        call char_addr
        pop af
        push hl
        call glyph_ptr
        ex de,hl
        pop hl
        ld b,8
pc_1:   ld a,(de)
        ld (hl),a
        inc de
        inc h
        djnz pc_1
        ld hl,pr_col
        inc (hl)
        pop bc
        pop de
        pop hl
        ret

; print_big: A = char, 16x16 (2x2 cells) at (pr_row,pr_col); advances 2 cols.
print_big:
        push hl
        push de
        push bc
        push af
        ld a,(pr_row)
        ld d,a
        ld a,(pr_col)
        ld e,a
        call attr_addr
        ld a,(pr_attr)
        ld (hl),a
        inc l
        ld (hl),a
        ld bc,31
        add hl,bc
        ld (hl),a
        inc l
        ld (hl),a
        pop af
        call glyph_ptr
        ld (big_g),hl
        call char_addr
        ld b,4
        call big_rows
        inc d
        call char_addr
        ld b,4
        call big_rows
        ld hl,pr_col
        inc (hl)
        inc (hl)
        pop bc
        pop de
        pop hl
        ret
big_rows:
        push de
bg_1:   push bc
        ld de,(big_g)
        ld a,(de)
        inc de
        ld (big_g),de
        ld c,a
        ld b,8
bg_2:   rlc c
        rl e
        rl d
        ld a,e
        rra
        rl e
        rl d
        djnz bg_2
        ld (hl),d
        inc l
        ld (hl),e
        dec l
        inc h
        ld (hl),d
        inc l
        ld (hl),e
        dec l
        inc h
        pop bc
        djnz bg_1
        pop de
        ret

; print_str: HL = string.  Codes: 0 end, 1 row col = AT, 2 attr, 3 big on, 4 big off
print_str:
        ld a,(hl)
        inc hl
        or a
        ret z
        cp 1
        jr z,ps_at
        cp 2
        jr z,ps_attr
        cp 3
        jr z,ps_big
        cp 4
        jr z,ps_small
        push af
        ld a,(pr_bigf)
        or a
        jr nz,ps_b
        pop af
        call print_char
        jr print_str
ps_b:   pop af
        call print_big
        jr print_str
ps_at:  ld a,(hl)
        inc hl
        ld (pr_row),a
        ld a,(hl)
        inc hl
        ld (pr_col),a
        jr print_str
ps_attr:
        ld a,(hl)
        inc hl
        ld (pr_attr),a
        jr print_str
ps_big: ld a,1
        ld (pr_bigf),a
        jr print_str
ps_small:
        xor a
        ld (pr_bigf),a
        jr print_str

; set_attr_run: D = row, E = col, B = count, A = attr
set_attr_run:
        push af
        call attr_addr
        pop af
sar_1:  ld (hl),a
        inc l
        djnz sar_1
        ret

; clear_box: D = top row, E = left col, B = height, C = width (chars); A = attr
clear_box:
        ld (cb_attr),a
cb_1:   push bc
        push de
        call attr_addr
        ld a,(cb_attr)
        ld b,c
cb_2:   ld (hl),a
        inc l
        djnz cb_2
        call char_addr
        ld b,8
cb_3:   push bc
        push hl
        ld b,c
        xor a
cb_4:   ld (hl),a
        inc l
        djnz cb_4
        pop hl
        inc h
        pop bc
        djnz cb_3
        pop de
        inc d
        pop bc
        djnz cb_1
        ret

; restore_rows: D = first char row, B = number of rows: copy mirror -> screen
restore_rows:
rr_1:   push bc
        push de
        ld e,0
        call char_addr
        ld b,8
rr_2:   push bc
        push hl
        ld a,h
        add a,MOFS
        ld d,a
        ld e,l
        ex de,hl
        ld bc,32
        ldir
        pop hl
        inc h
        pop bc
        djnz rr_2
        pop de
        push de
        ld e,0
        call attr_addr
        ld a,h
        add a,MOFS
        ld d,a
        ld e,l
        ex de,hl
        ld bc,32
        ldir
        pop de
        inc d
        pop bc
        djnz rr_1
        ret

pr_row:  DEFB 0
pr_col:  DEFB 0
pr_attr: DEFB $47
pr_bigf: DEFB 0
big_g:   DEFW 0
cb_attr: DEFB 0
