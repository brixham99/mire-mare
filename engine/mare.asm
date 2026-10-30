; ---------------------------------------------------------------- mare.asm
; The Night Mare.  By day she keeps to her home on Mare's Isle.  At night
; she roams the fen, moving one screen nearer Sabreman every MARE_STEP
; ticks; hoof-beats warn when she is a screen or two away.  In his room
; she gallops (3 px/tick) straight through the scenery.  Her touch costs a
; life and she wheels away.  She cannot be harmed - but with all four
; bridle pieces, one sabre stroke on Mare's Isle bridles her.
MARE_STEP   EQU 90

mare_init:
        ld a,ISLE_HOME
        ld (mare_room),a
        xor a
        ld (mare_here),a
        ld (mare_cool),a
        ld (mare_won),a
        ld a,MARE_STEP
        ld (mare_mt),a
        ret

; mare_room_enter: called by room_load
mare_room_enter:
        xor a
        ld (mare_here),a
        ld (mare_dx),a
        ld a,(mare_room)
        ld b,a
        ld a,(cur_room)
        cp b
        ret nz
        ld a,(px)
        cp 112
        ld a,8
        jr nc,mre_1
        ld a,216
mre_1:  ld (mare_x),a
        ld a,(py)
        ld (mare_y),a
        ld a,1
        ld (mare_here),a
        ld a,25
        ld (mare_cool),a        ; a moment's grace on arrival
        ret

; mare_dist -> A = screens between the Mare and Sabreman (Manhattan)
mare_dist:
        ld a,(mare_room)
        and 15
        ld b,a
        ld a,(cur_room)
        and 15
        call absdiff
        ld c,a
        ld a,(mare_room)
        rrca
        rrca
        rrca
        rrca
        and 15
        ld b,a
        ld a,(cur_room)
        rrca
        rrca
        rrca
        rrca
        and 15
        call absdiff
        add a,c
        ret

mare_tick:
        ld a,(mare_cool)
        or a
        jr z,mt_0
        dec a
        ld (mare_cool),a
mt_0:   ld a,(mare_here)
        or a
        jp nz,mare_act
        ld a,(night)
        or a
        ret z
        call mare_dist
        cp 3
        jr nc,mt_move
        ld b,15
        cp 1
        jr z,mt_h
        ld b,31
mt_h:   ld a,(tick)
        and b
        call z,sfx_hoof
mt_move:
        ld a,(mare_cool)
        or a
        ret nz
        ld hl,mare_mt
        dec (hl)
        ret nz
        ld (hl),MARE_STEP
        ; one screen toward Sabreman, x first
        ld a,(mare_room)
        and 15
        ld b,a
        ld a,(cur_room)
        and 15
        cp b
        jr z,mt_y
        ld a,(mare_room)
        jr c,mt_l
        inc a
        jr mt_set
mt_l:   dec a
        jr mt_set
mt_y:   ld a,(mare_room)
        ld b,a
        ld a,(cur_room)
        cp b
        ld a,b
        jr c,mt_u
        add a,MAP_W
        jr mt_set
mt_u:   sub MAP_W
mt_set: ld (mare_room),a
        ld b,a
        ld a,(cur_room)
        cp b
        ret nz
        call mare_room_enter
        jp sfx_neigh

; mare_act: she is in this room
mare_act:
        ld hl,mare_anim
        inc (hl)
        ld a,(mare_cool)
        or a
        jr nz,ma_hit            ; standing, pawing the ground
        ; gallop: 2 px every tick + 2 more every other tick
        ld a,(mare_dx)
        or a
        jr nz,ma_1
        ld a,(px)
        sub 4
        ld b,a
        ld a,(mare_x)
        cp b
        ld a,2
        jr c,ma_0
        ld a,-2
ma_0:   ld (mare_dx),a
ma_1:   call ma_stepx
        ld a,(tick)
        and 1
        call z,ma_stepx
        ; drift toward his row
        ld a,(py)
        ld b,a
        ld a,(mare_y)
        cp b
        jr z,ma_3
        jr c,ma_2
        dec a
        jr ma_3b
ma_2:   inc a
ma_3b:  ld (mare_y),a
ma_3:   ld a,(tick)
        and 7
        call z,sfx_hoof
ma_hit: ; sabre?
        ld a,(pattack)
        cp 5
        jr nz,ma_body
        ld a,(mare_y)
        ld b,a
        ld a,(py)
        call absdiff
        cp 18
        jr nc,ma_body
        ld a,(pface)
        cp 2
        ld a,(px)
        jr nz,ma_sl
        add a,24
        jr ma_sx
ma_sl:  sub 8
        jr c,ma_body
ma_sx:  ld b,a                  ; blade x
        ld a,(mare_x)
        cp b
        jr z,ma_in
        jr nc,ma_body
ma_in:  add a,32
        cp b
        jr c,ma_body
        ; struck
        ld a,(bridle)
        cp 15
        jr nz,ma_rear
        ld a,(g_desc)
        and $70
        cp R_ISLE*16
        jr nz,ma_rear
        ld a,1
        ld (mare_won),a
        ld (game_won),a
        ret
ma_rear:
        call sfx_neigh
        jr ma_flee
ma_body:
        ld a,(mare_cool)
        or a
        ret nz
        ld a,(pinv)
        or a
        ret nz
        ld a,(mare_y)
        ld b,a
        ld a,(py)
        call absdiff
        cp 16
        ret nc
        ld a,(mare_x)
        add a,16
        ld b,a
        ld a,(px)
        add a,12
        call absdiff
        cp 18
        ret nc
        ld a,1
        ld (p_hit),a
ma_flee:
        ; she wheels away into a neighbouring screen and rests a while
        xor a
        ld (mare_here),a
        ld a,(cur_room)
        ld b,a
        and 15
        cp 15
        ld a,b
        jr z,mf_1
        inc a
        jr mf_2
mf_1:   dec a
mf_2:   ld (mare_room),a
        ld a,200
        ld (mare_cool),a
        ld a,MARE_STEP
        ld (mare_mt),a
        ret

ma_stepx:
        ld a,(mare_dx)
        ld b,a
        ld a,(mare_x)
        add a,b
        cp 225
        jr c,ms_ok
        ld a,(mare_dx)          ; off an edge: turn
        neg
        ld (mare_dx),a
        ret
ms_ok:  ld (mare_x),a
        ret

; mare_draw.  On the Mere (all lily and water, no floor cells to paint) she
; first clears the cells her mask touches and gives them her own white ink,
; then draws on that cell-aligned shadow (y snapped to a cell), so she reads
; white against the lilies with no cell ever holding two inks.
mare_draw:
        ld a,(mare_here)
        or a
        ret z
        ld hl,rec_mare
        ld (ds_rec),hl
        ld a,(mare_anim)
        rrca
        rrca
        and 1
        ld b,a
        ld a,(mare_dx)
        rlca
        and 1                   ; 1 = going left
        add a,a
        or b
        ld (md_f),a
        ld a,(mare_y)
        add a,PLAY_TOP
        ld (md_y),a
        ld a,(g_desc)
        and $70
        cp R_MERE*16
        jr nz,md_draw
        ld a,(md_y)
        add a,4
        and $F8
        ld (md_y),a
        call mare_back
md_draw:
        ld a,(md_f)
        add a,a
        ld hl,mare_frames
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld a,(md_y)
        ld d,a
        ld a,(mare_x)
        ld e,a
        ld b,24
        ld c,4
        call draw_rt
        ld a,32
        ld (cs_w),a
        ld a,24
        ld (cs_h),a
        ld a,(md_y)
        ld d,a
        ld a,(mare_x)
        ld e,a
        ld a,$47
        jp color_spr

; mare_back: clear + ink the cells in mare_occ[frame][shift]
mare_back:
        ld a,(md_f)
        add a,a
        add a,a
        ld b,a
        ld a,(mare_x)
        and 6
        rrca
        add a,b
        add a,a
        ld hl,mare_occ
        call add_a_hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(md_y)
        rrca
        rrca
        rrca
        and $1F
        ld (mb_row),a
        ld b,3
mb_r:   push bc
        ld a,(mare_x)
        rrca
        rrca
        rrca
        and $1F
        ld (mb_col),a
        ld c,5
mb_c:   srl d
        rr e
        jr nc,mb_n
        ld a,(mb_col)
        cp 32
        jr nc,mb_n
        push de
        push bc
        ld e,a
        ld a,(mb_row)
        ld d,a
        call attr_addr
        ld a,(dim_mask)
        and $47
        ld (hl),a
        ld a,(mb_row)
        add a,a
        add a,a
        add a,a
        ld d,a
        call scr_addr
        ld b,8
        xor a
mb_z:   ld (hl),a
        inc h
        djnz mb_z
        pop bc
        pop de
mb_n:   ld hl,mb_col
        inc (hl)
        dec c
        jr nz,mb_c
        ld hl,mb_row
        inc (hl)
        pop bc
        djnz mb_r
        ret

mare_frames:
        DEFW SPR_mare_a,SPR_mare_b,SPR_mare_la,SPR_mare_lb
md_f:       DEFB 0
md_y:       DEFB 0
mb_row:     DEFB 0
mb_col:     DEFB 0

mare_room:  DEFB 0
mare_here:  DEFB 0
mare_x:     DEFB 0
mare_y:     DEFB 0
mare_dx:    DEFB 0
mare_anim:  DEFB 0
mare_cool:  DEFB 0
mare_mt:    DEFB 0
mare_won:   DEFB 0
