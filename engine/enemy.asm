; ---------------------------------------------------------------- enemy.asm
; Up to 3 creatures per room.  Slot (12 bytes):
;   state, type, x, y, dx, dy, timer, anim, spawn_x, spawn_y, hp, aux
; state: 0 none, 1 materialising, 2 alive, 3 dying, 4 dead (respawn timer)
; In state 2, timer is the hit cool-down; aux belongs to the AI.
; types: 0 wisp  1 toad  2 adder  3 heron  4 leech  5 boggart  6 monk
;        7 bog-body (rises at night)  8 bog-ox (24x24, cannot be killed)
;        9 night hag (the Mere, night only: blinks between screen edges)
ESLOT   EQU 12
ET_LEN  EQU 10

; etype_ptr: A = type -> HL = its etype entry (fa,fb,w,rows,attr,hp,size)
etype_ptr:
        ld l,a
        ld h,0
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de               ; x10
        ld de,etype
        add hl,de
        ret
etype:
        DEFW SPR_wisp_a,SPR_wisp_b
        DEFB 2,16,$43,1
        DEFW 96
        DEFW SPR_toad_a,SPR_toad_b
        DEFB 2,16,$44,1
        DEFW 96
        DEFW SPR_adder_a,SPR_adder_b
        DEFB 2,16,$46,1
        DEFW 96
        DEFW SPR_heron_a,SPR_heron_b
        DEFB 2,16,$45,1
        DEFW 96
        DEFW SPR_leech_a,SPR_leech_b
        DEFB 2,16,$42,1
        DEFW 96
        DEFW SPR_boggart_a,SPR_boggart_b
        DEFB 2,16,$46,2
        DEFW 96
        DEFW SPR_monk_a,SPR_monk_b
        DEFB 2,16,$47,1
        DEFW 96
        DEFW SPR_bogbody_a,SPR_bogbody_b
        DEFB 2,16,$44,3
        DEFW 96
        DEFW SPR_ox_a,SPR_ox_b
        DEFB 3,24,$42,255
        DEFW 192
        DEFW SPR_hag_a,SPR_hag_b
        DEFB 2,16,$45,1
        DEFW 96

; enemies_spawn: from the room record (g_desc+5/6) and gen_sp
enemies_spawn:
        xor a
        ld (leeched),a
        ld (clod_on),a
        ld hl,enemies
        ld b,3*ESLOT
        xor a
es_0:   ld (hl),a
        inc hl
        djnz es_0
        ld a,(g_desc+5)
        and $0F
        ld b,0
        call es_one
        ld a,(g_desc+5)
        rrca
        rrca
        rrca
        rrca
        and $0F
        ld b,1
        call es_one
        ld a,(g_desc+6)
        and $0F
        ld b,2
        call es_one
        ld a,(night)
        or a
        ret z
        ld a,(g_desc+6)
        rrca
        rrca
        rrca
        rrca
        and $0F
        ret z
        ld b,3                  ; night riser takes slot 2, at gen_sp[3]
; es_one: A = type+1 (0 = none), B = slot (3 = slot 2 with spawn point 3)
es_one: or a
        ret z
        dec a
        ld (t_type),a
        ld a,b
        add a,a
        ld hl,gen_sp
        call add_a_hl
        ld a,(hl)
        and $FE
        ld (t_x),a
        inc hl
        ld a,(hl)
        ld (t_y),a
        ld a,b
        cp 3
        jr c,es_2
        dec a
es_2:   ld l,a
        add a,a
        add a,l
        add a,a
        add a,a                 ; x12
        ld hl,enemies
        call add_a_hl
        push hl
        ld a,(t_type)
        call etype_ptr
        ld de,7
        add hl,de
        ld a,(hl)               ; hp
        ld (t_hp),a
        pop hl
        ld (hl),1               ; state
        inc hl
        ld a,(t_type)
        ld (hl),a
        inc hl
        ld a,(t_x)
        ld (hl),a
        inc hl
        ld a,(t_y)
        ld (hl),a
        inc hl
        ld (hl),2               ; dx
        inc hl
        ld (hl),0               ; dy
        inc hl
        ld a,(t_type)
        cp 7
        ld a,12
        jr nz,es_3
        ld a,40                 ; bog-bodies rise slowly
es_3:   ld (hl),a               ; timer
        inc hl
        ld (hl),0               ; anim
        inc hl
        ld a,(t_x)
        ld (hl),a
        inc hl
        ld a,(t_y)
        ld (hl),a
        inc hl
        ld a,(t_hp)
        ld (hl),a
        inc hl
        ld (hl),0               ; aux
        ret

; enemies_update: run AI for each slot through the ecur scratch copy
enemies_update:
        ld hl,enemies
        ld b,3
eu_1:   push bc
        push hl
        ld de,ecur
        ld bc,ESLOT
        ldir
        call enemy_logic
        pop de
        push de
        ld hl,ecur
        ld bc,ESLOT
        ldir
        pop hl
        ld de,ESLOT
        add hl,de
        pop bc
        djnz eu_1
        ret

; e_geom: size of the current type -> eg_w (px), eg_h, eg_xmax, eg_ymax
e_geom:
        ld a,(e_type)
        cp 8
        ld a,16
        jr nz,eg_1
        ld a,24
eg_1:   ld (eg_w),a
        ld (eg_h),a
        neg
        ld (eg_xmax),a          ; 256-w
        ld a,(eg_h)
        neg
        sub 80                  ; 176-h
        ld (eg_ymax),a
        ret

enemy_logic:
        ld a,(e_state)
        or a
        ret z
        call e_geom
        ld a,(e_state)
        cp 1
        jr z,el_spawn
        cp 3
        jr z,el_dying
        cp 4
        jr z,el_dead
        ld hl,e_anim
        inc (hl)
        ld a,(e_timer)
        or a
        jr z,el_ai
        dec a
        ld (e_timer),a
el_ai:  ld a,(e_type)
        add a,a
        ld hl,ai_tab
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        jp (hl)
ai_tab: DEFW ai_wisp,ai_toad,ai_adder,ai_heron,ai_leech,ai_boggart,ai_monk,ai_bogbody,ai_ox,ai_hag
el_spawn:
        ld hl,e_anim
        inc (hl)
        ld hl,e_timer
        dec (hl)
        ret nz
        ld a,2
        ld (e_state),a
        ret
el_dying:
        ld hl,e_anim
        inc (hl)
        ld hl,e_timer
        dec (hl)
        ret nz
        ld a,4
        ld (e_state),a
        ld a,150
        ld (e_timer),a
        ret
el_dead:
        ld hl,e_timer
        dec (hl)
        ret nz
        ld a,(e_sx)
        ld (e_x),a
        ld a,(e_sy)
        ld (e_y),a
        ld a,1
        ld (e_state),a
        ld a,12
        ld (e_timer),a
        xor a
        ld (e_aux),a
        ld a,(e_type)
        call etype_ptr
        ld de,7                 ; fa,fb (words), w, rows, attr, hp
        add hl,de
        ld a,(hl)
        ld (e_hp),a
        ret

; home_x: step e_x 2 px toward the player centre; home_y: 1 px
home_x: ld a,(px)
        add a,4
        and $FE
        ld b,a
        ld a,(e_x)
        cp b
        ret z
        jr c,hx_r
        sub 2
        ld (e_x),a
        ret
hx_r:   add a,2
        ld (e_x),a
        ret
home_y: ld a,(py)
        add a,4
        ld b,a
        ld a,(e_y)
        cp b
        ret z
        jr c,hy_d
        dec a
        ld (e_y),a
        ret
hy_d:   inc a
        ld (e_y),a
        ret

; ---- 0 will-o'-wisp: drifts toward Sabreman through everything
; by night they quicken: 3 steps in 4 across, every tick down/up
ai_wisp:
        ld a,(night)
        or a
        jr nz,aw_n
        ld a,(tick)
        and 1
        call z,home_x
        ld a,(tick)
        and 3
        call nz,home_y
        jp enemy_hit_check
aw_n:   ld a,(tick)
        and 3
        call nz,home_x
        call home_y
        jp enemy_hit_check

; ---- 1 toad: hop for 8 ticks, sit for 8; new heading every 32 or when blocked
ai_toad:
        ld a,(e_anim)
        and 31
        call z,rand_dir
        ld a,(e_anim)
        and 8
        jr nz,at_done
        call enemy_try_move
        call nz,rand_dir
at_done:
        jp enemy_hit_check

; ---- 2 adder: horizontal patrol; doubles speed when level with Sabreman
ai_adder:
        xor a
        ld (e_dy),a
        ld a,(e_dx)
        or a
        jr nz,ad_0
        ld a,2
        ld (e_dx),a
ad_0:   call level_y
        cp 12
        jr c,ad_go
        ld a,(tick)
        and 1
        jr nz,ad_done
ad_go:  call enemy_try_move
        jr z,ad_done
        ld a,(e_dx)
        neg
        ld (e_dx),a
ad_done:
        jp enemy_hit_check

; level_y -> A = |player centre y - creature centre y|
level_y:
        ld a,(eg_h)
        srl a
        ld b,a
        ld a,(e_y)
        add a,b
        ld b,a
        ld a,(py)
        add a,12
        jp absdiff
; level_x -> A = |player centre x - creature centre x|
level_x:
        ld a,(eg_w)
        srl a
        ld b,a
        ld a,(e_x)
        add a,b
        ld b,a
        ld a,(px)
        add a,12
        jp absdiff

; ---- 3 heron: stalks slowly; lunges 4 px/tick when in line with Sabreman
ai_heron:
        ld a,(e_aux)
        or a
        jr z,ah_idle
        dec a
        ld (e_aux),a
        cp 40
        jr c,ah_done            ; resting after a lunge
        cp 56
        jr nc,ah_done           ; rearing back: a fair warning before the lunge
        call enemy_try_move
        jr z,ah_done
        ld a,40
        ld (e_aux),a
        jr ah_done
ah_idle:
        call level_y
        cp 6
        jr nc,ah_v
        call level_x
        cp 100
        jr nc,ah_walk
        ld a,(px)
        ld b,a
        ld a,(e_x)
        cp b
        ld a,3
        jr c,ah_h
        ld a,-3
ah_h:   ld (e_dx),a
        xor a
        ld (e_dy),a
        jr ah_lunge
ah_v:   call level_x
        cp 6
        jr nc,ah_walk
        call level_y
        cp 80
        jr nc,ah_walk
        ld a,(py)
        add a,8
        ld b,a
        ld a,(e_y)
        cp b
        ld a,3
        jr c,ah_vv
        ld a,-3
ah_vv:  ld (e_dy),a
        xor a
        ld (e_dx),a
ah_lunge:
        ld a,66                 ; 10 ticks rearing, 16 of lunge, 40 of rest
        ld (e_aux),a
        call sfx_swing
        jr ah_done
ah_walk:
        ld a,(e_anim)
        and 63
        call z,rand_dir
        ld a,(tick)
        and 3
        jr nz,ah_done
        call enemy_try_move
        call nz,rand_dir
ah_done:
        jp enemy_hit_check

; ---- 4 leech: creeps toward Sabreman; clings (slowing him) until slashed
ai_leech:
        ld a,(e_aux)
        or a
        jr z,al_creep
        inc a
        ld (e_aux),a
        cp 200
        jr c,al_on
        ; drained: costs a life and drops off
        ld a,1
        ld (p_hit),a
        jr al_drop
al_on:  ld a,(px)
        add a,4
        and $FE
        ld (e_x),a
        ld a,(py)
        add a,6
        ld (e_y),a
        ld a,1
        ld (leeched),a
        ld a,(pattack)
        cp 5
        ret nz
        ; any swing knocks it off
        call sfx_kill
al_drop:
        xor a
        ld (leeched),a
        ld (e_aux),a
        ld a,3
        ld (e_state),a
        ld a,8
        ld (e_timer),a
        ret
al_creep:
        ld a,(tick)
        and 3
        call z,home_x
        ld a,(tick)
        and 1
        call z,home_y
        jp enemy_hit_check

; ---- 5 boggart: lurches about; bursts at Sabreman when close.  2 hits.
ai_boggart:
        ld a,(e_aux)
        or a
        jr z,ab_wander
        dec a
        ld (e_aux),a
        cp 30
        jr c,ab_done
        call enemy_try_move
        jr ab_done
ab_wander:
        call level_x
        cp 60
        jr nc,ab_w2
        call level_y
        cp 50
        jr nc,ab_w2
        ; burst: 4 px/tick toward him for 12 ticks then rest 30
        ld a,(px)
        add a,4
        ld b,a
        ld a,(e_x)
        cp b
        ld a,4
        jr c,ab_1
        ld a,-4
ab_1:   ld (e_dx),a
        ld a,(py)
        add a,4
        ld b,a
        ld a,(e_y)
        cp b
        ld a,2
        jr c,ab_2
        ld a,-2
ab_2:   ld (e_dy),a
        ld a,42
        ld (e_aux),a
        jr ab_done
ab_w2:  call bog_throw
        ld a,(e_anim)
        and 31
        call z,rand_dir
        ld a,(tick)
        and 1
        jr nz,ab_done
        call enemy_try_move
        call nz,rand_dir
ab_done:
        jp enemy_hit_check

; bog_throw: level with Sabreman and a fair way off, sometimes lob a clod
bog_throw:
        ld a,(clod_on)
        or a
        ret nz
        call level_y
        cp 10
        ret nc
        call level_x
        cp 36
        ret c
        cp 150
        ret nc
        call rand
        and 15
        ret nz
        ld a,(e_x)
        add a,4
        and $FE
        ld (clod_x),a
        ld a,(e_y)
        add a,4
        ld (clod_y),a
        ld a,(px)
        ld b,a
        ld a,(e_x)
        cp b
        ld a,4
        jr c,bth_1
        ld a,-4
bth_1:  ld (clod_dx),a
        ld a,40
        ld (clod_on),a          ; also its life in ticks
        jp sfx_clod

; clod_tick: fly, stop at scenery or edges, hurt Sabreman, or be swatted
clod_tick:
        ld a,(clod_on)
        or a
        ret z
        dec a
        ld (clod_on),a
        ret z
        ld a,(clod_dx)
        ld b,a
        ld a,(clod_x)
        add a,b
        cp 248
        jr nc,ck_gone
        ld (clod_x),a
        add a,4
        ld b,a
        ld a,(clod_y)
        add a,4
        ld c,a
        call tile_at
        and F_SOLID
        jr nz,ck_gone
        ; height match with Sabreman's body
        ld a,(clod_y)
        add a,4
        ld b,a
        ld a,(py)
        add a,14
        call absdiff
        cp 12
        ret nc
        ld a,(pattack)
        or a
        jr z,ck_body
        ; the sabre bats it away when it is near the blade
        ld a,(pface)
        cp 2
        ld a,(px)
        jr nz,ck_l
        add a,26
        jr ck_s
ck_l:   sub 2
ck_s:   ld b,a
        ld a,(clod_x)
        add a,4
        call absdiff
        cp 12
        jr nc,ck_body
        call sfx_hit
        ld a,1
        ld b,4
        call add_score          ; 10
        jr ck_gone
ck_body:
        ld a,(pinv)
        or a
        ret nz
        ld a,(px)
        add a,12
        ld b,a
        ld a,(clod_x)
        add a,4
        call absdiff
        cp 9
        ret nc
        ld a,1
        ld (p_hit),a
ck_gone:
        xor a
        ld (clod_on),a
        ret

clod_draw:
        ld a,(clod_on)
        or a
        ret z
        ld hl,rec_clod
        ld (ds_rec),hl
        ld hl,SPR_clod_a
        ld a,(clod_x)
        ld e,a
        call frame_gfx
        ld a,(clod_y)
        add a,PLAY_TOP
        ld d,a
        ld a,(clod_x)
        ld e,a
        ld b,8
        ld c,2
        call draw_spr
        ld a,8
        ld (cs_w),a
        ld (cs_h),a
        ld a,(clod_y)
        add a,PLAY_TOP
        ld d,a
        ld a,(clod_x)
        ld e,a
        ld a,(dim_mask)
        and $46
        jp color_spr

clod_on: DEFB 0
clod_x:  DEFB 0
clod_y:  DEFB 0
clod_dx: DEFB 0

; ---- 6 drowned monk: follows walls (turns clockwise when blocked)
ai_monk:
        ld a,(tick)
        and 1
        jr nz,am_done
        ld a,(e_anim)
        and 127
        call z,rand_dir
        call enemy_try_move
        jr z,am_done
        ; turn clockwise: (dx,dy) -> (-dy,dx)
        ld a,(e_dy)
        neg
        ld b,a
        ld a,(e_dx)
        ld (e_dy),a
        ld a,b
        ld (e_dx),a
am_done:
        jp enemy_hit_check

; ---- 7 bog-body: risen from the pool at night, shambles after Sabreman
ai_bogbody:
        ld a,(tick)
        and 3
        call z,home_x
        ld a,(tick)
        and 1
        call z,home_y
        jp enemy_hit_check

; ---- 8 bog-ox: wanders; charges along a row when level.  Can't be killed.
ai_ox:
        ld a,(e_aux)
        or a
        jr z,ao_idle
        dec a
        ld (e_aux),a
        cp 40
        jr c,ao_done
        cp 100
        jr nc,ao_done           ; pawing the ground and bellowing: a fair warning
        call enemy_try_move
        jr z,ao_done
        ld a,39                 ; hit something: stop and rest
        ld (e_aux),a
        jr ao_done
ao_idle:
        call level_y
        cp 8
        jr nc,ao_w
        ld a,(px)
        ld b,a
        ld a,(e_x)
        cp b
        ld a,4
        jr c,ao_1
        ld a,-4
ao_1:   ld (e_dx),a
        xor a
        ld (e_dy),a
        ld a,110                ; 10 ticks of warning, then 60 of charge
        ld (e_aux),a
        call sfx_ox
        jr ao_done
ao_w:   ld a,(e_anim)
        and 63
        call z,rand_dir
        ld a,(tick)
        and 3
        jr nz,ao_done
        call enemy_try_move
        call nz,rand_dir
ao_done:
        jp enemy_hit_check

; ---- 9 night hag: blinks in at the screen edge away from Sabreman, level
; with him, and shrieks straight across (3 px/tick) through everything; at
; the far edge she blinks out and in again.  Gone at dawn.
ai_hag:
        ld a,(night)
        or a
        jr nz,ag_0
        ld (e_state),a          ; daylight: she is simply not there
        ret
ag_0:   ld a,(e_aux)
        or a
        jr nz,ag_fly
ag_blink:
        ld a,1
        ld (e_aux),a
        ld a,(px)
        cp 116
        ld a,236
        ld b,-2
        jr c,ag_1
        ld a,4
        ld b,2
ag_1:   ld (e_x),a
        ld a,b
        ld (e_dx),a
        ld a,(py)
        add a,4
        ld (e_y),a
        ld a,1
        ld (e_state),a          ; sparkle at the new edge, then fly
        ld a,16
        ld (e_timer),a
        jp sfx_hag
ag_fly: ld a,(e_dx)
        ld b,a
        ld a,(e_x)
        add a,b
        ld c,a
        ld a,(tick)
        and 1
        ld a,c
        jr z,ag_2
        add a,b
ag_2:   ld (e_x),a
        cp 2
        jr c,ag_blink
        cp 238
        jr nc,ag_blink
        ld a,(tick)
        and 3
        call z,home_y
        jp enemy_hit_check

rand_dir:
        call rand
        and 3
        add a,a
        ld hl,dir_tab
        call add_a_hl
        ld a,(hl)
        ld (e_dx),a
        inc hl
        ld a,(hl)
        ld (e_dy),a
        ret
dir_tab: DEFB 2,0, $FE,0, 0,2, 0,$FE

; enemy_try_move: step by (dx,dy) if in bounds and not into scenery -> Z if moved
enemy_try_move:
        ld a,(e_dx)
        ld b,a
        ld a,(e_x)
        add a,b
        ld b,a
        ld a,(eg_xmax)
        cp b
        jr c,etm_no
        ld a,(e_dy)
        ld c,a
        ld a,(e_y)
        add a,c
        ld c,a
        ld a,(eg_ymax)
        cp c
        jr c,etm_no
        push bc
        ld a,b
        add a,3
        ld b,a
        ld a,(eg_h)
        sub 2
        add a,c
        ld c,a
        call tile_at
        and F_SOLID
        jr nz,etm_pop
        ld a,(eg_w)
        sub 7
        add a,b
        ld b,a
        call tile_at
        and F_SOLID
        jr nz,etm_pop
        pop bc
        ld a,b
        ld (e_x),a
        ld a,c
        ld (e_y),a
        xor a
        ret
etm_pop:
        pop bc
etm_no: ld a,1
        or a
        ret

; enemy_hit_check: the sabre (left/right) hurts; touching Sabreman sets p_hit.
; Horizontal maths in half-pixels with a +8 bias so nothing goes negative.
enemy_hit_check:
        ld a,(e_state)
        cp 2
        ret nz
        ld a,(eg_w)
        srl a
        ld b,a
        ld a,(e_x)
        add a,b                 ; centre x (px), may pass 255 for none
        rra
        add a,8
        ld (eh_ex),a
        ld a,(eg_h)
        sub 16
        srl a
        ld (eh_ext),a           ; extra reach for big creatures
        ld a,(eg_h)
        srl a
        ld b,a
        ld a,(e_y)
        add a,b
        ld b,a
        ld a,(py)
        add a,14
        call absdiff
        ld (eh_dy),a
        ld a,(pattack)
        or a
        jp z,ehc_body
        ld a,(eh_ext)
        add a,20                ; the swing reaches a little above and below him, so a
        ld b,a                  ; creature closing in vertically meets the blade first
        ld a,(eh_dy)
        cp b
        jp nc,ehc_body
        ld a,(px)
        srl a
        ld b,a
        ld a,(pface)
        cp 2
        ld a,b
        jr nz,ehc_l
        add a,19
        jr ehc_s
ehc_l:  add a,9
ehc_s:  ld b,a
        ld a,(eh_ex)
        call absdiff
        ld b,a
        ld a,(eh_ext)
        srl a
        add a,8
        cp b
        jp c,ehc_body
        jp z,ehc_body
        ; a hit
        ld a,(e_timer)
        or a
        ret nz                  ; still reeling from the last one
        ld a,(e_type)
        cp 8
        jr z,ehc_ox
        ld hl,e_hp
        dec (hl)
        jr z,ehc_kill
        ld a,12
        ld (e_timer),a
        ld a,(e_type)
        cp 5
        jr nz,ehc_kb
        ld a,29                 ; a struck boggart's charge is broken: it rests
        ld (e_aux),a
ehc_kb: ld a,(pface)            ; and every survivor is knocked back
        cp 2
        ld a,4
        jr z,ehc_k1
        ld a,-4
ehc_k1: ld (e_dx),a
        xor a
        ld (e_dy),a
        call enemy_try_move
        call enemy_try_move
        call enemy_try_move
        jp sfx_hit
ehc_ox: ; the ox only staggers back
        ld a,20
        ld (e_timer),a
        ld a,30
        ld (e_aux),a
        ld a,(pface)
        cp 2
        ld a,8
        jr z,ehc_o1
        ld a,-8
ehc_o1: ld (e_dx),a
        xor a
        ld (e_dy),a
        call enemy_try_move
        call enemy_try_move
        jp sfx_hit
ehc_kill:
        ld a,3
        ld (e_state),a
        ld a,8
        ld (e_timer),a
        call sfx_kill
        ld a,(e_type)
        ld b,a
        ld a,1
        cp b
        ld b,3
        jp add_score            ; 100
ehc_body:
        ld a,(pinv)
        or a
        ret nz
        ld a,(eh_ext)
        add a,15
        ld b,a
        ld a,(eh_dy)
        cp b
        ret nc
        ld a,(px)
        srl a
        add a,14
        ld b,a
        ld a,(eh_ex)
        call absdiff
        ld b,a
        ld a,(eh_ext)
        srl a
        add a,7
        cp b
        ret c
        ret z
        ld a,(e_type)
        cp 4
        jr z,ehc_leech
        ld a,1
        ld (p_hit),a
        ret
ehc_leech:
        ld a,(leeched)
        or a
        ret nz                  ; only one leech at a time
        ld a,1
        ld (e_aux),a
        ld (leeched),a
        jp sfx_squelch

; enemies_draw
enemies_draw:
        ld hl,enemies
        ld de,rec_en
        ld b,3
ed_1:   push bc
        push hl
        push de
        ld (ds_rec),de
        ld de,ecur
        ld bc,ESLOT
        ldir
        call enemy_draw1
        pop hl
        ld de,9
        add hl,de
        ex de,hl
        pop hl
        ld bc,ESLOT
        add hl,bc
        pop bc
        djnz ed_1
        ret

enemy_draw1:
        ld a,(e_state)
        or a
        ret z
        cp 4
        ret z
        cp 2
        jr z,ed_alive
        ; materialising / dying: sparkle (pre-shifted 16x16)
        ld a,(e_anim)
        rrca
        and 1
        add a,a
        ld hl,spark_frames
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld a,(e_x)
        ld e,a
        call frame_gfx
        ld a,$47
        ld (ed_attr),a
        ld a,16
        ld (ed_h),a
        ld a,3
        ld (ed_wb),a
        jr ed_go
ed_alive:
        ; reeling creatures blink
        ld a,(e_timer)
        and 2
        ret nz
        ld a,(e_type)
        call etype_ptr
        ld de,4
        add hl,de
        ld a,(hl)               ; w bytes
        inc a
        ld (ed_wb),a
        inc hl
        ld a,(hl)               ; rows
        ld (ed_h),a
        inc hl
        ld a,(dim_mask)
        and (hl)
        ld (ed_attr),a
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)               ; size of one shifted frame
        ; index = (frame*4 + shift)
        ld a,(e_anim)
        rrca
        rrca
        rrca
        and 1
        add a,a
        add a,a
        ld b,a
        ld a,(e_x)
        and 6
        rrca
        add a,b
        ld b,a
        ld a,(e_type)
        add a,a
        ld hl,ctype_ptr
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        inc b
ed_m:   dec b
        jr z,ed_go
        add hl,de
        jr ed_m
ed_go:  ld a,(e_y)
        add a,PLAY_TOP
        ld d,a
        ld a,(e_x)
        ld e,a
        ld a,(ed_h)
        ld b,a
        ld a,(ed_wb)
        ld c,a
        call draw_spr
        ld a,(ed_h)
        ld (cs_h),a
        ld a,(ed_wb)
        dec a
        add a,a
        add a,a
        add a,a
        ld (cs_w),a
        ld a,(e_y)
        add a,PLAY_TOP
        ld d,a
        ld a,(e_x)
        ld e,a
        ld a,(ed_attr)
        jp color_spr

spark_frames:
        DEFW SPR_spark_a,SPR_spark_b

enemies: DEFS 3*ESLOT
ecur:
e_state: DEFB 0
e_type:  DEFB 0
e_x:     DEFB 0
e_y:     DEFB 0
e_dx:    DEFB 0
e_dy:    DEFB 0
e_timer: DEFB 0
e_anim:  DEFB 0
e_sx:    DEFB 0
e_sy:    DEFB 0
e_hp:    DEFB 0
e_aux:   DEFB 0
t_type:  DEFB 0
t_x:     DEFB 0
t_y:     DEFB 0
t_hp:    DEFB 0
eh_ex:   DEFB 0
eh_dy:   DEFB 0
eh_ext:  DEFB 0
ed_attr: DEFB 0
ed_h:    DEFB 0
ed_wb:   DEFB 0
eg_w:    DEFB 0
eg_h:    DEFB 0
eg_xmax: DEFB 0
eg_ymax: DEFB 0
leeched: DEFB 0
