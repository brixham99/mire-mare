; ---------------------------------------------------------------- player.asm
; Sabreman: 24x24, 4 directions x 2 walk frames + left/right sabre swing.
; Feet box (collision with scenery) = x+6..x+17, y+18..y+23.

player_update:
        ld a,(pinv)
        or a
        jr z,pu_0
        dec a
        ld (pinv),a
pu_0:   ld a,(px)
        ld (prev_px),a
        ld a,(py)
        ld (prev_py),a
        call pu_timers
        call read_input
        call input_filter
        ld (pin),a
        xor a
        ld (pmoved),a
        ; --- sabre swing in progress?
        ld a,(pattack)
        or a
        jr z,pu_1
        dec a
        ld (pattack),a
        jp pu_after
pu_1:   ld a,(pin)
        and IN_FIRE
        ld b,a
        ld a,(pfire_prev)
        ld c,a
        ld a,b
        ld (pfire_prev),a
        or a
        jr z,pu_move
        ld a,c
        or a
        jr nz,pu_move
        ld a,6
        ld (pattack),a
        call sfx_swing
        jp pu_after
pu_move:
        ; --- terrain speed: shallow mire, or deep sinking, halves speed
        ld a,(leeched)
        or a
        jr nz,pu_slow
        ld a,(pu_water)
        or a
        jr nz,pu_go
        call feet_flags
        and F_SLOW
        jr nz,pu_slow
        ld a,(psink)
        cp 8
        jr c,pu_go
pu_slow:
        ld a,(tick)
        and 1
        jr z,pu_go
        ; still turn to face the input direction while held back
        jp pu_after
pu_go:  call pu_step
        ld a,(room_changed)
        or a
        ret nz
        ld a,(pu_swift)
        or a
        call nz,pu_step
        ld a,(room_changed)
        or a
        ret nz
        jr pu_stepped
pu_step:
        ld a,(pin)
        bit 3,a
        call nz,try_up
        ld a,(room_changed)
        or a
        ret nz
        ld a,(pin)
        bit 2,a
        call nz,try_down
        ld a,(room_changed)
        or a
        ret nz
        ld a,(pin)
        bit 1,a
        call nz,try_left
        ld a,(room_changed)
        or a
        ret nz
        ld a,(pin)
        bit 0,a
        jp nz,try_right
        ret
pu_stepped:
        ld a,(pmoved)
        or a
        jr z,pu_after
        ld hl,panim
        inc (hl)
        ; squelch every 8th step in mire
        call feet_flags
        and F_SLOW|F_SINK
        jr z,pu_after
        ld a,(panim)
        and 7
        call z,sfx_squelch
pu_after:
        ; --- sinking in deep bog
        ld a,(pu_water)
        or a
        jr nz,pu_unsink
        call feet_flags
        and F_SINK
        jr z,pu_unsink
        ld a,(tick)
        and 3
        jr nz,pu_items
        ld a,(psink)
        inc a
        ld (psink),a
        cp SINK_MAX
        jr c,pu_items
        ld a,1
        ld (p_hit),a            ; drowned
        jr pu_items
pu_unsink:
        ld a,(psink)
        or a
        jr z,pu_items
        dec a
        ld (psink),a
pu_items:
        jp item_check

; feet_flags -> A = flags of the tile under the feet centre
feet_flags:
        ld a,(px)
        add a,12
        ld b,a
        ld a,(py)
        add a,21
        ld c,a
        jp tile_at

; feet_free: B = x, C = y (candidate) -> Z if the feet box is clear. Keeps BC.
feet_free:
        push bc
        ld a,b
        add a,6
        ld b,a
        ld a,c
        add a,18
        ld c,a
        call tile_at
        and F_SOLID
        jr nz,ff_x
        ld a,b
        add a,11
        ld b,a
        call tile_at
        and F_SOLID
        jr nz,ff_x
        ld a,c
        add a,5
        ld c,a
        call tile_at
        and F_SOLID
        jr nz,ff_x
        ld a,b
        sub 11
        ld b,a
        call tile_at
        and F_SOLID
ff_x:   pop bc
        ret

; probe2: two points (B1,C) (B2,C) given as B = x1, D = x2, C = y -> Z if both clear
probe_col:
        push de
        call tile_at
        pop de
        and F_SOLID
        ret nz
        ld b,d
        call tile_at
        and F_SOLID
        ret

try_left:
        ld a,3
        ld (pdir),a
        ld (pface),a
        ld a,(px)
        cp 2
        jr c,tl_edge
        sub 2
        ld b,a
        ld a,(py)
        ld c,a
        call feet_free
        ret nz
        ld a,b
        ld (px),a
        ld a,1
        ld (pmoved),a
        ret
tl_edge:
        ld a,(py)
        add a,18
        ld c,a
        ld b,0
        call tile_at
        and F_SOLID
        ret nz
        ld a,(py)
        add a,23
        ld c,a
        ld b,0
        call tile_at
        and F_SOLID
        ret nz
        ld a,PX_MAX
        ld (px),a
        ld a,(cur_room)
        dec a
        jp change_room

try_right:
        ld a,2
        ld (pdir),a
        ld (pface),a
        ld a,(px)
        cp PX_MAX
        jr nc,tr_edge
        add a,2
        ld b,a
        ld a,(py)
        ld c,a
        call feet_free
        ret nz
        ld a,b
        ld (px),a
        ld a,1
        ld (pmoved),a
        ret
tr_edge:
        ld a,(py)
        add a,18
        ld c,a
        ld b,255
        call tile_at
        and F_SOLID
        ret nz
        ld a,(py)
        add a,23
        ld c,a
        ld b,255
        call tile_at
        and F_SOLID
        ret nz
        xor a
        ld (px),a
        ld a,(cur_room)
        inc a
        jp change_room

try_up:
        ld a,1
        ld (pdir),a
        ld a,(py)
        cp 2
        jr c,tu_edge
        sub 2
        ld c,a
        ld a,(px)
        ld b,a
        call feet_free
        ret nz
        ld a,c
        ld (py),a
        ld a,1
        ld (pmoved),a
        ret
tu_edge:
        ld a,(px)
        add a,6
        ld b,a
        add a,11
        ld d,a
        ld c,0
        call probe_col
        ret nz
        ld a,PY_MAX
        ld (py),a
        ld a,(cur_room)
        sub MAP_W
        jp change_room

try_down:
        xor a
        ld (pdir),a
        ld a,(py)
        cp PY_MAX
        jr nc,td_edge
        add a,2
        ld c,a
        ld a,(px)
        ld b,a
        call feet_free
        ret nz
        ld a,c
        ld (py),a
        ld a,1
        ld (pmoved),a
        ret
td_edge:
        ld a,(px)
        add a,6
        ld b,a
        add a,11
        ld d,a
        ld c,175
        call probe_col
        ret nz
        xor a
        ld (py),a
        ld a,(cur_room)
        add a,MAP_W
        jp change_room

; change_room: A = new room (px/py already set to the entry position).
; If the entry spot is blocked in the new room, bounce back.
change_room:
        push af
        ld a,(cur_room)
        ld (prev_room),a
        xor a
        ld (psink),a
        ld (leeched),a
        pop af
        call room_load
        ld a,1
        ld (room_changed),a
        ld a,(px)
        ld b,a
        ld a,(py)
        ld c,a
        call feet_free
        jr nz,cr_back
        ld a,(px)
        ld (entry_x),a
        ld a,(py)
        ld (entry_y),a
        ret
cr_back:
        ld a,(prev_px)
        ld (px),a
        ld a,(prev_py)
        ld (py),a
        ld a,(prev_room)
        jp room_load

; player_hit: called after enemies when touched or drowned
player_hit:
        ld a,(pinv)
        or a
        jr z,ph_1
        ld a,(psink)            ; invulnerable, but drowning still counts
        cp SINK_MAX
        ret c
ph_1:   call sfx_death
        ld b,6
ph_fl:  push bc
        ld a,b
        and 1
        add a,a                 ; red flash on the border
        out ($FE),a
        halt
        halt
        pop bc
        djnz ph_fl
        xor a
        out ($FE),a
        ld hl,lives
        dec (hl)
        ld a,1
        ld (hud_dirty),a
        ld a,(entry_x)
        ld (px),a
        ld a,(entry_y)
        ld (py),a
        xor a
        ld (psink),a
        ld (pattack),a
        ld a,50
        ld (pinv),a
        ; the screen's creatures fall back to their lairs and re-form there,
        ; so a death is not followed straight away by another
        xor a
        ld (clod_on),a
        ld (leeched),a
        ld hl,enemies
        ld b,3
ph_e:   ld a,(hl)
        cp 2
        jr nz,ph_e1
        ld (hl),4               ; respawn wait...
        push hl
        ld de,6
        add hl,de
        ld (hl),25              ; ...of one second, then a sparkle at the lair
        pop hl
ph_e1:  ld de,ESLOT
        add hl,de
        djnz ph_e
        ret

; player_draw
player_draw:
        ld hl,rec_player
        ld (ds_rec),hl
        ld a,(pinv)
        and 2
        ret nz                  ; blink while invulnerable
        ld a,(pattack)
        or a
        jr z,pd_walk
        ld a,(pface)
        sub 2                   ; 0 right, 1 left
        add a,8
        jr pd_frame
pd_walk:
        ld a,(pdir)
        add a,a
        ld b,a
        ld a,(panim)
        rrca
        rrca
        and 1
        or b
pd_frame:
        add a,a
        ld hl,player_frames
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld a,(px)
        ld e,a
        call frame_gfx
        ld a,(psink)
        ld b,a
        ld a,(py)
        add a,PLAY_TOP
        add a,b
        ld d,a
        ld a,24
        sub b
        ld b,a
        ld a,(px)
        ld e,a
        ld c,4
        jp draw_spr

player_frames:
        DEFW SPR_sab_down_a,SPR_sab_down_b,SPR_sab_up_a,SPR_sab_up_b
        DEFW SPR_sab_right_a,SPR_sab_right_b,SPR_sab_left_a,SPR_sab_left_b
        DEFW SPR_sab_hit_r,SPR_sab_hit_l

px:         DEFB 0
py:         DEFB 0
pdir:       DEFB 0          ; 0 down 1 up 2 right 3 left
pface:      DEFB 2          ; last horizontal facing (2/3)
panim:      DEFB 0
pattack:    DEFB 0
psink:      DEFB 0
pinv:       DEFB 0
pin:        DEFB 0
pfire_prev: DEFB 0
pmoved:     DEFB 0
pk_flag:    DEFB 0
entry_x:    DEFB 0
entry_y:    DEFB 0
prev_px:    DEFB 0
prev_py:    DEFB 0
prev_room:  DEFB 0
