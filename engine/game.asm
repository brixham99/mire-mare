; ---------------------------------------------------------------- game.asm
game_new:
        ld hl,score_init
        ld de,score
        ld bc,6
        ldir
        ld hl,$ACE1             ; fixed seed: a game is a pure function of its inputs
        ld (seed),hl
        ld a,START_LIVES
        ld (lives),a
        xor a
        ld (gems),a
        ld (bridle),a
        ld (psink),a
        ld (pattack),a
        ld (panim),a
        ld (pdir),a
        ld (game_won),a
        ld (has_lantern),a
        ld (has_key),a
        ld (causeway_up),a
        ld (leeched),a
        ld (tick),a
        ld hl,pu_water
        ld b,6
gn_0:   ld (hl),a
        inc hl
        djnz gn_0
        ld hl,0
        ld (msg_pending),hl
        ld (msg_next),hl
        ld (gtick),hl
        ld hl,room_flags
        ld b,NUM_ROOMS
gn_1:   ld (hl),a
        inc hl
        djnz gn_1
        ld a,2
        ld (pface),a
        ld a,40
        ld (pinv),a
        call clock_init
        call mare_init
        xor a
        call cls_all
        call hud_init
        ld a,START_X
        ld (px),a
        ld (entry_x),a
        ld (prev_px),a
        ld a,START_Y
        ld (py),a
        ld (entry_y),a
        ld (prev_py),a
        IF DEMO
        call demo_start
        ENDIF
        ld a,START_ROOM
        jp room_load

game_run:
gr_loop:
        call wait_tick
        call erase_all
        call enemies_draw
        call clod_draw
        call mare_draw
        call player_draw
        ld hl,tick
        inc (hl)
        ld hl,(gtick)
        inc hl
        ld (gtick),hl
        xor a
        ld (room_changed),a
        ld (p_hit),a
        call player_update
        ld a,(room_changed)
        or a
        jr nz,gr_post
        call enemies_update
        call clod_tick
        call mare_tick
        ld a,(p_hit)
        or a
        call nz,player_hit
        call bud_tick
        call clock_tick
gr_post:
        call hud_update
        ld hl,(msg_pending)
        ld a,h
        or l
        call nz,show_message
        IF DEMO
        ELSE
        call check_pause
        ENDIF
        ld a,(game_won)
        or a
        jp nz,ending
        ld a,(lives)
        or a
        jr nz,gr_loop
        ret

; ending: the Mare is bridled.  At 100% a second verse follows.
ending:
        call sfx_quest
        ld b,50
en_0:   halt
        djnz en_0
        xor a
        call cls_all
        ld hl,end_text
        call print_str
        call calc_pct
        cp 100
        jr nz,en_1
        ld hl,end_text_b
        call print_str
en_1:   ld hl,menu_tune
        call play_tune
        ld b,200
en_2:   halt
        djnz en_2
        xor a
        jp cls_all
end_text:
        DEFB 1,3,6,2,$42,"--------------------"
        DEFB 1,4,10,2,$47,"THE MARE IS"
        DEFB 1,5,9,2,$46,3,"BRIDLED",4
        DEFB 1,8,4,2,$46,"SABREMAN RIDES HER HOME"
        DEFB 1,9,5,"ACROSS THE SLEEPING FEN"
        DEFB 1,11,6,2,$45,"AND THE MIRE DREAMS"
        DEFB 1,12,11,"NO MORE",0
end_text_b:
        DEFB 1,15,5,2,$43,"EVERY LIGHT IS GATHERED"
        DEFB 1,16,5,"EVERY SCREEN IS WALKED"
        DEFB 1,18,5,2,$46,"THE FEN IS WHOLE AGAIN"
        DEFB 1,20,6,2,$42,"--------------------",0

; calc_pct -> A = completion: screens seen/4 + lights*3/4 + pieces*5 + mare*10
calc_pct:
        ld hl,room_flags
        ld bc,NUM_ROOMS*256
cpc_0:   bit 1,(hl)
        jr z,cpc_1
        inc c
cpc_1:   inc hl
        djnz cpc_0
        srl c
        srl c                   ; seen / 4  (max 40)
        ld a,(gems)
        ld b,a
        add a,a
        add a,b
        srl a
        srl a                   ; lights * 3/4 (max 30)
        add a,c
        ld c,a
        ld a,(bridle)
        ld b,4
cpc_2:   rrca
        jr nc,cpc_3
        ld d,a
        ld a,c
        add a,5
        ld c,a
        ld a,d
cpc_3:   djnz cpc_2
        ld a,(mare_won)
        or a
        ld a,c
        ret z
        add a,10
        ret

; game_over: percentage + rating screen (Ultimate style), updates the hi score
game_over:
        ld b,25
go_0:   halt
        djnz go_0
        ld d,5
        ld e,3
        ld b,14
        ld c,26
        xor a
        call clear_box
        ld hl,go_text
        call print_str
        ld a,(game_won)
        or a
        jr z,go_lost
        ld hl,go_won
        call print_str
go_lost:
        call calc_pct
        ld (go_pct),a
        ld a,10
        ld (pr_row),a
        ld a,20
        ld (pr_col),a
        ld a,$46
        ld (pr_attr),a
        ld a,(go_pct)
        call print_dec3
        ld a,'%'
        call print_char
        ; rating
        ld a,(go_pct)
        ld b,0
go_r:   cp 25
        jr c,go_r2
        sub 25
        inc b
        jr go_r
go_r2:  ld a,b
        cp 5
        jr c,go_r3
        ld b,4
go_r3:  ld a,b
        add a,a
        ld hl,rank_tab
        call add_a_hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        call print_str
        ; hi score
        ld hl,score
        ld de,hiscore
        ld b,6
go_h:   ld a,(de)
        cp (hl)
        jr c,go_new
        jr nz,go_keep
        inc hl
        inc de
        djnz go_h
        jr go_keep
go_new: ld hl,score
        ld de,hiscore
        ld bc,6
        ldir
        call hud_hi
go_keep:
        call wait_no_key
        ld b,0
go_w:   halt
        call any_key
        jr nz,go_out
        call read_input
        and IN_FIRE
        jr nz,go_out
        djnz go_w
go_out: call wait_no_key
        ld a,(go_pct)
        cp 100
        ret c
        jp saga

; saga: the 100% closing scroll (Ending B).  Lines rise from the foot of the
; screen one character row at a time, Ultimate style; any key ends it.
saga:
        ld a,1
        ld (saga_on),a
        xor a
        call cls_all
        ld hl,saga_text
sg_l:   ld a,(hl)
        cp $FF
        jr z,sg_end
        push hl
        call scroll_up
        pop hl
        ld a,(hl)
        inc hl
        ld (pr_attr),a
        ld a,(hl)
        inc hl
        ld (pr_col),a
        ld a,21
        ld (pr_row),a
sg_c:   ld a,(hl)
        inc hl
        or a
        jr z,sg_d
        push hl
        call print_char
        pop hl
        jr sg_c
sg_d:   push hl
        ld b,16
sg_w:   halt
        djnz sg_w
        pop hl
        call any_key
        jr z,sg_l
sg_end: ld b,0
sg_h:   halt
        call any_key
        jr nz,sg_x
        djnz sg_h
sg_x:   ld a,2
        ld (saga_on),a
        call wait_no_key
        xor a
        jp cls_all

; scroll_up: character rows 1-21 move up one row (bitmap then attributes,
; row by row, so a row's ink always matches its pixels); row 21 is cleared
scroll_up:
        halt
        ld c,8
su_1:   push bc
        ld d,c
        ld e,0
        call scr_addr
        pop bc
        push bc
        push hl
        ld a,c
        add a,8
        ld d,a
        ld e,0
        call scr_addr
        pop de
        ld bc,32
        ldir
        pop bc
        inc c
        ld a,c
        and 7
        jr nz,su_1
        ; whole row done: its attributes follow
        push bc
        ld a,c
        sub 8                   ; dest row y
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl               ; row*32 = y*4
        ld de,$5800
        add hl,de
        ld d,h
        ld e,l
        ld hl,32
        add hl,de
        ld bc,32
        ldir
        pop bc
        ld a,c
        cp 168
        jr nz,su_1
su_2:   ld d,c
        ld e,0
        call scr_addr
        ld b,32
        xor a
su_3:   ld (hl),a
        inc l
        djnz su_3
        inc c
        ld a,c
        cp 176
        jr nz,su_2
        ld hl,$5800+21*32
        ld b,32
su_4:   ld (hl),0
        inc hl
        djnz su_4
        ret
saga_on: DEFB 0
saga_text:
        DEFB $47,0,0
        DEFB $46,6,"THE SAGA OF SABREMAN",0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $47,6,"SABREMAN HAS RIDDEN",0
        DEFB $47,7,"HIS NIGHTMARE HOME",0
        DEFB $47,0,0
        DEFB $45,6,"EVERY LIGHT GATHERED",0
        DEFB $45,6,"EVERY SCREEN WALKED",0
        DEFB $45,5,"EVERY PIECE RECLAIMED",0
        DEFB $47,0,0
        DEFB $44,8,"THE MIRE SLEEPS",0
        DEFB $44,5,"THE FEN IS WHOLE AGAIN",0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $43,7,"THE SAGA IS ENDED",0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $46,11,"SLEEP WELL",0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $47,0,0
        DEFB $FF

; print_dec3: A (0-255) as up to 3 digits, right aligned in 3 cells
print_dec3:
        ld c,' '
        ld b,'0'-1
pd3_1:  inc b
        sub 100
        jr nc,pd3_1
        add a,100
        push af
        ld a,b
        cp '0'
        jr z,pd3_2
        ld c,'0'
        call print_char
        jr pd3_3
pd3_2:  ld a,' '
        call print_char
pd3_3:  pop af
        ld b,'0'-1
pd3_4:  inc b
        sub 10
        jr nc,pd3_4
        add a,10
        push af
        ld a,b
        cp c
        jr nz,pd3_5
        cp '0'
        jr nz,pd3_5
        ld a,' '
pd3_5:  call print_char
        pop af
        add a,'0'
        jp print_char

go_text:
        DEFB 1,5,3,2,$46,"--------------------------"
        DEFB 1,7,8,2,$47,3,"GAME OVER",4
        DEFB 1,10,5,2,$45,"QUEST COMPLETED"
        DEFB 1,13,8,2,$47,"OVERALL RATING",0
rank_tab:
        DEFW rk0,rk1,rk2,rk3,rk4
rk0:    DEFB 1,15,10,2,$44,"BOG TROTTER",0
rk1:    DEFB 1,15,10,2,$44,"FEN WALKER",0
rk2:    DEFB 1,15,9,2,$44,"MIRE STRIDER",0
rk3:    DEFB 1,15,10,2,$44,"MARSH LORD",0
rk4:    DEFB 1,15,11,2,$46,"ULTIMATE",0
go_won: DEFB 1,7,8,2,$46,3,"QUEST DONE",4,0

go_pct:   DEFB 0

; ---- game state
score_init: DEFB "000000"
score:    DEFB "000000"
hiscore:  DEFB "010000"
lives:    DEFB 0
gems:     DEFB 0
bridle:   DEFB 0
tick:     DEFB 0
room_changed: DEFB 0
p_hit:    DEFB 0
gtick:    DEFW 0
game_won: DEFB 0
