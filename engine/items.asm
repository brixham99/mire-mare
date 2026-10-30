; ---------------------------------------------------------------- items.asm
; Pick-ups, mire-blooms (power-ups) and their timers, message boxes.

; item_check: anything under Sabreman's feet?
item_check:
        ld a,(px)
        add a,12
        ld b,a
        ld a,(py)
        add a,21
        ld c,a
        call tile_at
        and F_ITEM
        ret z
        ld a,(hl)
        ld (ic_tile),a
        ld (ic_ptr),hl
        cp TILE_BUD
        jr nz,ic_take
        ld a,(bud_phase)
        ld (ic_eff),a
ic_take:
        call item_under
        ld hl,(ic_ptr)
        ld (hl),a
        ld a,(cur_room)
        ld hl,room_flags
        call add_a_hl
        set 0,(hl)
        srl b
        srl b
        srl b
        srl b
        srl c
        srl c
        srl c
        srl c
        call redraw_tile
        ld a,$FF
        ld (bud_tx),a
        ld a,1
        ld (hud_dirty),a
        ld a,(ic_tile)
        cp TILE_MARSHLIGHT
        jr nz,ic_1
        ld hl,gems
        inc (hl)
        ld a,5
        ld b,3
        call add_score          ; 500
        jp sfx_pickup
ic_1:   cp TILE_BUD
        jp z,bloom
        ld hl,bridle
        ld de,msg_bit
        cp TILE_BIT
        jr nz,ic_2
        set 0,(hl)
        jr ic_piece
ic_2:   ld de,msg_rein
        cp TILE_REIN
        jr nz,ic_3
        set 1,(hl)
        jr ic_piece
ic_3:   ld de,msg_head
        cp TILE_HEADSTALL
        jr nz,ic_4
        set 2,(hl)
        jr ic_piece
ic_4:   ld de,msg_buckle
        cp TILE_BUCKLE
        jr nz,ic_5
        set 3,(hl)
ic_piece:
        ld (msg_pending),de
        ld a,(bridle)
        cp 15
        jr nz,ic_p2
        ld de,msg_whole
        ld (msg_next),de
ic_p2:  ld a,2
        ld b,2
        call add_score          ; 2000
        jp sfx_quest
ic_5:   ld de,msg_lantern
        ld hl,has_lantern
        cp TILE_LANTERN
        jr z,ic_flag
        ld de,msg_key
        ld hl,has_key
        cp TILE_KEY
        jr z,ic_flag
        ld de,msg_lever
        ld hl,causeway_up
ic_flag:
        ld (hl),1
        ld (msg_pending),de
        ld a,1
        ld b,2
        call add_score          ; 1000
        jp sfx_quest

; bloom: the bud's colour when taken decides the effect
bloom:  call sfx_pickup
        ld a,(ic_eff)
        or a
        jr nz,bl_1
        ld a,250
        ld (pu_water),a
        ret
bl_1:   dec a
        jr nz,bl_2
        ld a,250
        ld (pu_swift),a
        ret
bl_2:   dec a
        jr nz,bl_3
        ld a,200
        ld (pinv),a
        ld (pu_ward),a
        ret
bl_3:   dec a
        jr nz,bl_4
        ld a,(lives)
        cp MAX_LIVES
        ret nc
        inc a
        ld (lives),a
        ret
bl_4:   dec a
        jr nz,bl_5
        ld a,125
        ld (pu_fever),a
        ret
bl_5:   ld a,50
        ld (pu_drowse),a
        ret

; pu_timers: count the bloom effects down; border shows the active one
pu_timers:
        ld hl,pu_water
        ld b,5
        ld c,0
ptm_0:   ld a,(hl)
        or a
        jr z,ptm_1
        dec (hl)
        ld a,b
        ld c,a                  ; remember which (5..1)
ptm_1:   inc hl
        djnz ptm_0
        ld a,c
        ld hl,pu_border
        call add_a_hl
        ld a,(hl)
        ld (border),a
        out ($FE),a
        ret
pu_border:
        DEFB 0,7,2,3,6,5        ; none, drowse, fever, ward, swift, water

; input_filter: A = input -> A filtered (drowse freezes, fever reverses)
input_filter:
        ld b,a
        ld a,(pu_drowse)
        or a
        jr z,if_1
        xor a
        ret
if_1:   ld a,(pu_fever)
        or a
        ld a,b
        ret z
        and IN_FIRE
        ld c,a
        ld a,b
        and 5                   ; right, down
        add a,a
        or c
        ld c,a
        ld a,b
        and 10                  ; left, up
        rrca
        or c
        ret

; bud_find: is there an untaken mire-bloom in this room?
bud_find:
        ld a,$FF
        ld (bud_tx),a
        ld a,(item_tx)
        cp $FF
        ret z
        ld b,a
        ld a,(item_ty)
        ld c,a
        call cell_hl
        ld a,(hl)
        cp TILE_BUD
        ret nz
        ld a,b
        ld (bud_tx),a
        ld a,c
        ld (bud_ty),a
        ret

; bud_tick: cycle the bloom's colour every 8 ticks
bud_tick:
        ld a,(tick)
        and 7
        ret nz
        ld a,(bud_phase)
        inc a
        cp 6
        jr c,bt_1
        xor a
bt_1:   ld (bud_phase),a
        ld a,(bud_tx)
        cp $FF
        ret z
        ld a,(bud_phase)
        ld hl,bud_cols
        call add_a_hl
        ld a,(dim_mask)
        and (hl)
        push af
        ld a,(bud_tx)
        ld b,a
        ld a,(bud_ty)
        ld c,a
        pop af
        jp set_tile_attr
bud_cols:
        DEFB $45,$46,$43,$44,$42,$47    ; water swift ward life fever drowse

; show_message: (msg_pending) = print_str text; box over the play area
show_message:
        ld hl,(msg_pending)
        push hl
        ld hl,0
        ld (msg_pending),hl
        call erase_all
        ld d,8
        ld e,3
        ld b,9
        ld c,26
        xor a
        call clear_box
        pop hl
        call print_str
        ld b,90
sm_1:   halt
        djnz sm_1
        ld d,8
        ld b,9
        call restore_rows
        ld hl,(msg_next)
        ld (msg_pending),hl
        ld hl,0
        ld (msg_next),hl
        ret

        INCLUDE "data/messages.asm"

ic_tile:    DEFB 0
ic_eff:     DEFB 0
ic_ptr:     DEFW 0
bud_tx:     DEFB $FF
bud_ty:     DEFB 0
bud_phase:  DEFB 0
pu_water:   DEFB 0          ; order matters (pu_timers)
pu_swift:   DEFB 0
pu_ward:    DEFB 0
pu_fever:   DEFB 0
pu_drowse:  DEFB 0
border:     DEFB 0
has_lantern: DEFB 0
has_key:    DEFB 0
causeway_up: DEFB 0
msg_pending: DEFW 0
msg_next:   DEFW 0
