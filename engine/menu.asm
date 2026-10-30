; ---------------------------------------------------------------- menu.asm
; Ultimate-style framed control menu.
menu:
        xor a
        call cls_all
        call draw_frame
        ld hl,menu_text
        call print_str
        call menu_hilite
        ld hl,menu_tune
        call play_tune
        call wait_no_key
mn_loop:
        halt
        ld hl,seed              ; stir the RNG while waiting
        inc (hl)
        ld a,$F7                ; 1-4
        in a,($FE)
        cpl
        and $0F
        jr z,mn_start
        ld b,0
mn_b:   rra
        jr c,mn_set
        inc b
        jr mn_b
mn_set: ld a,b
        ld (ctrl_type),a
        call menu_hilite
        call sfx_menu
        call wait_no_key
        jr mn_loop
mn_start:
        ld a,$EF                ; 0
        in a,($FE)
        rra
        jr c,mn_loop
        call sfx_pickup
        jp wait_no_key

menu_hilite:
        ld c,0
mh_1:   ld a,c
        add a,a
        add a,7
        ld d,a
        ld e,4
        ld b,24
        ld a,(ctrl_type)
        cp c
        ld a,$46                ; selected: bright yellow
        jr z,mh_2
        ld a,$05                ; others: cyan
mh_2:   push bc
        call set_attr_run
        pop bc
        inc c
        ld a,c
        cp 4
        jr nz,mh_1
        ret

; draw_frame: double border - bright yellow knotwork outside, red inside
draw_frame:
        ld a,$46
        ld (pr_attr),a
        ld d,0
        call frame_hline
        ld d,23
        call frame_hline
        ld d,1
df_1:   ld a,d
        ld (pr_row),a
        xor a
        ld (pr_col),a
        ld a,CH_FRV
        call print_char
        ld a,31
        ld (pr_col),a
        ld a,CH_FRV
        call print_char
        inc d
        ld a,d
        cp 23
        jr nz,df_1
        ld hl,frame_corners
        call print_str
        ; inner red rule: rows 1 and 22, cols 1 and 30 (attrs over blank cells)
        ld a,$02
        ld (pr_attr),a
        ld d,1
        call inner_hline
        ld d,22
        call inner_hline
        ret
frame_hline:
        ld a,d
        ld (pr_row),a
        ld a,1
        ld (pr_col),a
        ld b,30
fh_1:   ld a,CH_FRH
        call print_char
        djnz fh_1
        ret
inner_hline:
        ld a,d
        ld (pr_row),a
        ld a,1
        ld (pr_col),a
        ld b,30
ih_1:   ld a,CH_EMPTY+0
        ld a,'-'
        call print_char
        djnz ih_1
        ret
frame_corners:
        DEFB 2,$47
        DEFB 1,0,0,CH_FRC,1,0,31,CH_FRC,1,23,0,CH_FRC,1,23,31,CH_FRC,0

menu_text:
        DEFB 1,3,7,2,$44,3,"MIRE MARE",4
        DEFB 1,7,4,"1  KEYBOARD"
        DEFB 1,9,4,"2  KEMPSTON JOYSTICK"
        DEFB 1,11,4,"3  CURSOR JOYSTICK"
        DEFB 1,13,4,"4  INTERFACE II"
        DEFB 1,16,4,2,$47,"0  START GAME"
        DEFB 1,18,3,2,$05,"Q LEFT W RIGHT R UP E DOWN"
        DEFB 1,19,3,"T FIRE        ENTER PAUSE"
        DEFB 1,21,8,2,$42,$7F," 1985 A.C.G.",0
