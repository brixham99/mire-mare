; ---------------------------------------------------------------- roomgen.asm
; Procedural room builder.  Every one of the 160 screens is described by a
; 7-byte record in world_tab (data/world.asm, written by tools/world.py):
;   +0  exits N1 E2 S4 W8 | region<<4 | bit7 causeway room
;   +1  seed (chosen by tools/world.py so the room validates)
;   +2  lily sides (lo nibble) | door sides (hi nibble)
;   +3  item kind (lo) | bit4 item in pool | bit5 doors are crypt doors
;   +4  pool type (lo) | clump count (hi)
;   +5  enemy slot0 type+1 (lo) | slot1 (hi)
;   +6  enemy slot2 type+1 (lo) | night spawn type+1 (hi)
; room_gen: A = room -> roombuf filled, item_tx/ty, gen_sp (4 x (x,y) px),
; pool_cx/cy.  Deterministic: uses its own generator seed.
REC_LEN     EQU 7
R_MERE      EQU 4
R_ISLE      EQU 5

room_gen:
        ld (g_room),a
        ld l,a
        ld h,0
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        sbc hl,de               ; x7 (carry clear after add)
        ld de,world_tab
        add hl,de
        ld de,g_desc
        ld bc,REC_LEN
        ldir
        ld a,(g_desc+1)
        ld h,a
        ld a,(g_room)
        ld l,a
        set 0,l
        ld (gseed),hl
        ; region table entry -> g_reg (8 bytes)
        ld a,(g_desc)
        rrca
        rrca
        rrca
        rrca
        and 7
        ld (g_region),a
        add a,a
        add a,a
        add a,a
        ld hl,region_tab
        call add_a_hl
        ld de,g_reg
        ld bc,8
        ldir
        ld a,(g_desc)
        and 15
        ld (g_exits),a
        ld a,$FF
        ld (item_tx),a
        ld (pool_cx),a
        ; fill: floor, or water inside a Mere room
        ld hl,roombuf
        ld b,176
        ld a,TILE_FLOOR
gf_1:   ld (hl),a
        inc hl
        djnz gf_1
        ld a,(g_region)
        cp R_MERE
        jr nz,g_border
        ld b,1
        ld c,1
        ld d,14
        ld e,9
        ld a,TILE_WATER
        call fill_rect
g_border:
        ld c,0
gb_y:   ld b,0
gb_x:   ld a,c
        or a
        jr z,gb_w
        cp 10
        jr z,gb_w
        ld a,b
        or a
        jr z,gb_w
        cp 15
        jr nz,gb_n
gb_w:   call wall_tile
        call cell_hl
        ld (hl),a
gb_n:   inc b
        ld a,b
        cp 16
        jr nz,gb_x
        inc c
        ld a,c
        cp 11
        jr nz,gb_y
        ; bulges on land: thicken the wall here and there
        ld a,(g_region)
        cp R_MERE
        jr z,g_exits_
        ld b,1
gbl_1:  ld c,1
        call bulge
        ld c,9
        call bulge
        inc b
        ld a,b
        cp 15
        jr nz,gbl_1
        ld c,2
gbl_2:  ld b,1
        call bulge
        ld b,14
        call bulge
        inc c
        ld a,c
        cp 9
        jr nz,gbl_2
g_exits_:
        ; ---- exit gaps
        ld hl,gap_tab
        ld a,1
        ld (g_side),a
ge_1:   ld a,(g_exits)
        ld c,a
        ld a,(g_side)
        and c
        jr z,ge_next
        push hl
        call gap_tile           ; A = tile for this side's gap
        pop hl
        push hl
        ld (rf_tile),a
        ld b,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld e,(hl)
        ld a,(rf_tile)
        call fill_any
        pop hl
ge_next:
        ld de,4
        add hl,de
        ld a,(g_side)
        add a,a
        ld (g_side),a
        cp 16
        jr nz,ge_1
        ; ---- Mere: lily paths from each exit to the centre, causeway
        ld a,(g_region)
        cp R_MERE
        jr nz,g_pool
        ld hl,path_tab
        ld a,1
        ld (g_side),a
gm_1:   ld a,(g_exits)
        ld c,a
        ld a,(g_side)
        and c
        jr z,gm_n
        push hl
        ld b,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld e,(hl)
        ld a,TILE_NIGHTLILY
        call fill_any
        pop hl
gm_n:   ld de,4
        add hl,de
        ld a,(g_side)
        add a,a
        ld (g_side),a
        cp 16
        jr nz,gm_1
        ld b,6                  ; centre hub of lilies
        ld c,4
        ld d,4
        ld e,3
        ld a,TILE_NIGHTLILY
        call fill_any
        ld a,(g_desc)
        and $80
        jp z,g_items
        ld b,6
        ld c,0
        ld d,4
        ld e,11
        ld a,TILE_CAUSEWAYSUNK
        call fill_any
        jp g_items
        ; ---- terrain pool
g_pool: ld a,(g_desc+4)
        and 15
        jp z,g_clumps
        dec a
        jr nz,gp_2
        ; 1: mire 5x3 in a quadrant
        call quadrant
        ld d,5
        ld e,3
        ld a,TILE_SHALLOW
        call pool_rect
        jp g_clumps
gp_2:   dec a
        jr nz,gp_3
        ; 2: mire 7x5 with a bog core 3x2
        call quadrant
        ld d,7
        ld e,5
        ld a,TILE_SHALLOW
        call pool_rect
        ld d,3
        ld e,2
        ld a,TILE_BOG
        call bog_rect
        jp g_clumps
gp_3:   dec a
        jr nz,gp_4
        ; 3: bog 4x3 with a mire rim 6x5
        call quadrant
        ld d,4
        ld e,3
        ld a,TILE_BOG
        call bog_rect
        ld d,6
        ld e,5
        ld a,TILE_SHALLOW
        call pool_rect
        jp g_clumps
gp_4:   dec a
        jr nz,gp_5
        ; 4: central mire across the hub
        ld a,8
        ld (pool_cx),a
        ld a,5
        ld (pool_cy),a
        ld d,6
        ld e,3
        ld a,TILE_SHALLOW
        call pool_rect
        jr g_clumps
gp_5:   dec a
        jr nz,gp_6
        ; 5: two mire pools
        call quadrant
        ld d,5
        ld e,3
        ld a,TILE_SHALLOW
        call pool_rect
        call quadrant
        ld d,4
        ld e,3
        ld a,TILE_SHALLOW
        call pool_rect
        jr g_clumps
gp_6:   dec a
        jr nz,gp_7
        ; 6: a still pond (deep water, impassable) in a quadrant
        call quadrant
        ld d,4
        ld e,2
        ld a,TILE_WATER
        call bog_rect
        ld a,$FF
        ld (pool_cx),a
        jr g_clumps
gp_7:   ; 7: flooded floor: a wide sheet of shallow water
        ld a,8
        ld (pool_cx),a
        ld a,5
        ld (pool_cy),a
        ld d,12
        ld e,7
        ld a,TILE_SHALLOW
        call pool_rect
        ; ---- clumps of scenery, kept off the exit cross
g_clumps:
        ld a,(g_desc+4)
        rrca
        rrca
        rrca
        rrca
        and 15
        or a
        jr z,g_scatter
        ld b,a
gc_1:   push bc
        ld e,14
        call rnd_n
        inc a
        ld (g_x),a
        ld e,9
        call rnd_n
        inc a
        ld (g_y),a
        call grnd
        and 3
        ld hl,clump_w
        call add_a_hl
        ld a,(hl)
        ld (g_w),a
        call grnd
        and 1
        inc a
        ld (g_h),a
        ld e,3
        call rnd_n
        ld hl,g_reg+2
        call add_a_hl
        ld a,(hl)
        ld (rf_tile),a
        ld a,1
        ld (rf_prot),a
        ld a,(g_x)
        ld b,a
        ld a,(g_y)
        ld c,a
        ld a,(g_h)
        ld e,a
        ld a,(g_w)
        ld d,a
        call rect_go
        pop bc
        djnz gc_1
        ; ---- scattered walkable decorations
g_scatter:
        ld b,5
gs_1:   push bc
        call rnd_cell
        call cell_hl
        ld a,(hl)
        cp TILE_FLOOR
        jr nz,gs_2
        call grnd
        and 1
        add a,5
        push hl
        ld hl,g_reg
        call add_a_hl
        ld a,(hl)
        pop hl
        ld (hl),a
gs_2:   pop bc
        djnz gs_1
        ; ---- item
g_items:
        ld a,(g_desc+3)
        and 15
        jr z,g_spawn
        ld hl,item_tiles-1
        call add_a_hl
        ld a,(hl)
        ld (g_t),a
        ld a,(g_desc+3)
        and 16
        jr z,gi_rnd
        ld a,(pool_cx)
        cp $FF
        jr z,gi_rnd
        ld b,a
        ld a,(pool_cy)
        ld c,a
        jr gi_put
gi_rnd: ld d,60
gi_1:   push de
        call rnd_cell
        call cell_hl
        pop de
        ld a,(hl)
        cp TILE_FLOOR
        jr z,gi_put
        ld a,(g_region)
        cp R_MERE
        jr nz,gi_2
        ld a,(hl)
        cp TILE_NIGHTLILY
        jr z,gi_put
gi_2:   dec d
        jr nz,gi_1
        jr g_spawn
gi_put: call cell_hl
        ld a,(g_t)
        ld (hl),a
        ld a,b
        ld (item_tx),a
        ld a,c
        ld (item_ty),a
        ; ---- enemy spawn points (4: three slots + night riser)
g_spawn:
        ld hl,gen_sp
        ld b,4
gsp_1:  push bc
        push hl
        ld d,80
gsp_2:  push de
        ld e,12
        call rnd_n
        add a,2
        ld b,a
        ld e,7
        call rnd_n
        add a,2
        ld c,a
        pop de
        call entry_zone
        jr nz,gsp_3
        call cell_hl
        ld a,(hl)
        cp TILE_FLOOR
        jr z,gsp_ok
        cp TILE_TUSSOCK
        jr z,gsp_ok
        cp TILE_FLAGSTONE
        jr z,gsp_ok
        cp TILE_NIGHTLILY
        jr z,gsp_ok
gsp_3:  dec d
        jr nz,gsp_2
gsp_ok: pop hl
        ld a,b
        add a,a
        add a,a
        add a,a
        add a,a
        ld (hl),a
        inc hl
        ld a,c
        add a,a
        add a,a
        add a,a
        add a,a
        ld (hl),a
        inc hl
        pop bc
        djnz gsp_1
        ; the night riser climbs out of the bog pool if there is one
        ld a,(pool_cx)
        cp $FF
        ret z
        add a,a
        add a,a
        add a,a
        add a,a
        ld (gen_sp+6),a
        ld a,(pool_cy)
        add a,a
        add a,a
        add a,a
        add a,a
        ld (gen_sp+7),a
        ret

; entry_zone: B = x, C = y (tiles) -> NZ if too near an entrance
entry_zone:
        ld a,c
        cp 3
        jr c,ez_ns
        cp 8
        jr nc,ez_ns
        ld a,b
        cp 4
        jr c,ez_yes
        cp 12
        jr nc,ez_yes
ez_ns:  ld a,b
        cp 5
        jr c,ez_no
        cp 11
        jr nc,ez_no
        ld a,c
        cp 3
        jr c,ez_yes
        cp 8
        jr nc,ez_yes
ez_no:  xor a
        ret
ez_yes: or 1
        ret

; gap_tile: tile for the exit gap on side (g_side)
gap_tile:
        ld a,(g_desc+2)
        rrca
        rrca
        rrca
        rrca
        and 15
        ld c,a
        ld a,(g_side)
        and c
        jr z,gt_1
        ld a,(g_desc+3)
        and 32
        ld a,TILE_SPIRITDOOR
        ret z
        ld a,TILE_CRYPTDOOR
        ret
gt_1:   ld a,(g_region)
        cp R_MERE
        ld a,TILE_NIGHTLILY
        ret z
        ld a,(g_desc+2)
        and 15
        ld c,a
        ld a,(g_side)
        and c
        ld a,TILE_FLOOR
        ret z
        ld a,(g_desc)
        and $80
        jr z,gt_lily
        ld a,(g_side)
        and 5                   ; causeway runs north-south
        jr z,gt_lily
        ld a,TILE_CAUSEWAYSUNK
        ret
gt_lily:
        ld a,TILE_NIGHTLILY
        ret

; wall_tile -> A: region wall, 1 in 4 the second variant.  Keeps BC.
wall_tile:
        push hl
        call grnd
        and 3
        ld a,(g_reg)
        jr nz,wt_x
        ld a,(g_reg+1)
wt_x:   pop hl
        ret

; bulge: B,C = inner cell next to the wall; 1 in 4 becomes wall unless protected
bulge:  call grnd
        and 3
        ret nz
        call is_prot
        ret nz
        call wall_tile
        call cell_hl
        ld (hl),a
        ret

; is_prot: B = x, C = y -> NZ if the cell is on the hub or an exit arm. Keeps BC.
is_prot:
        ld a,(g_exits)
        ld e,a
        ld a,b
        cp 6
        jr c,ip_h
        cp 10
        jr nc,ip_h
        ; x in 6..9
        ld a,c
        cp 4
        jr c,ip_n
        cp 7
        jr c,ip_yes
        ld a,e                  ; y > 6: south arm
        and 4
        ret
ip_n:   ld a,e
        and 1
        ret
ip_h:   ld a,c
        cp 4
        jr c,ip_no
        cp 7
        jr nc,ip_no
        ld a,b
        cp 6
        jr c,ip_w
        ld a,e
        and 2
        ret
ip_w:   ld a,e
        and 8
        ret
ip_yes: or 1
        ret
ip_no:  xor a
        ret

; quadrant: picks a random quadrant centre -> B,C and pool_cx/cy
quadrant:
        call grnd
        and 3
        add a,a
        ld hl,quad_tab
        call add_a_hl
        ld b,(hl)
        inc hl
        ld c,(hl)
        ld a,b
        ld (pool_cx),a
        ld a,c
        ld (pool_cy),a
        ret

; pool_rect: centre pool_cx/cy, D = w, E = h, A = tile; floor cells only
pool_rect:
        ld (rf_tile),a
        xor a
        ld (rf_prot),a
        jr pr_go
; bog_rect: same but never on the exit cross
bog_rect:
        ld (rf_tile),a
        ld a,1
        ld (rf_prot),a
pr_go:  ld a,(pool_cx)
        ld b,d
        srl b
        sub b
        ld b,a
        ld a,(pool_cy)
        ld c,e
        srl c
        sub c
        ld c,a
        jr rect_go

; fill_rect / fill_any: B,C = x0,y0, D = w, E = h, A = tile
; fill_any writes everything (no clipping rules); rect_go writes only floor
; cells inside 1..14 x 1..9, and (rf_prot) keeps it off the exit cross.
fill_rect:
        ld (rf_tile),a
        xor a
        ld (rf_prot),a
        jr rect_go
fill_any:
        ld (rf_tile),a
        ld a,2
        ld (rf_prot),a
rect_go:
        ld a,b
        ld (rg_x0),a
rg_y:   ld a,(rg_x0)
        ld b,a
        push de
rg_x:   push de
        call rect_cell
        pop de
        inc b
        dec d
        jr nz,rg_x
        pop de
        inc c
        dec e
        jr nz,rg_y
        ret
rect_cell:
        ld a,(rf_prot)
        cp 2
        jr z,rc_put
        ld a,b
        dec a
        cp 14
        ret nc                  ; x outside 1..14 (also catches negatives)
        ld a,c
        dec a
        cp 9
        ret nc
        ld a,(rf_prot)
        or a
        jr z,rc_fl
        call is_prot
        ret nz
rc_fl:  call cell_hl
        ld a,(hl)
        cp TILE_FLOOR
        ret nz
rc_put: call cell_hl
        ld a,(rf_tile)
        ld (hl),a
        ret

; cell_hl: B = x, C = y -> HL = roombuf cell.  Keeps A? no; keeps BC, DE.
cell_hl:
        push af
        ld a,c
        add a,a
        add a,a
        add a,a
        add a,a
        add a,b
        ld hl,roombuf
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        pop af
        ret

; rnd_cell -> B,C random interior cell
rnd_cell:
        ld e,14
        call rnd_n
        inc a
        ld b,a
        push bc
        ld e,9
        call rnd_n
        inc a
        pop bc
        ld c,a
        ret

; rnd_n: E = n -> A = random 0..n-1.  Keeps BC.
rnd_n:  push bc
        call grnd
        ld c,a
        ld hl,0
        ld d,0
        ld b,8
rn_1:   add hl,hl
        sla c
        jr nc,rn_2
        add hl,de
rn_2:   djnz rn_1
        ld a,h
        pop bc
        ret

; grnd: generator xorshift -> A (also stored in g_r).  Keeps BC, DE.
grnd:   push hl
        ld hl,(gseed)
        ld a,h
        rra
        ld a,l
        rra
        xor h
        ld h,a
        ld a,l
        rra
        ld a,h
        rra
        xor l
        ld l,a
        xor h
        ld h,a
        ld (gseed),hl
        ld (g_r),a
        pop hl
        ret

gap_tab:    ; x0,y0,w,h per side N E S W
        DEFB 6,0,4,1, 15,4,1,3, 6,10,4,1, 0,4,1,3
path_tab:
        DEFB 6,1,4,4, 10,4,5,3, 6,7,4,3, 1,4,5,3
quad_tab:
        DEFB 3,2, 12,2, 3,8, 12,8
clump_w:
        DEFB 1,2,2,3
item_tiles:
        DEFB TILE_MARSHLIGHT,TILE_BIT,TILE_REIN,TILE_HEADSTALL,TILE_BUCKLE
        DEFB TILE_LANTERN,TILE_KEY,TILE_LEVER,TILE_BUD

g_room:   DEFB 0
g_desc:   DEFS REC_LEN
g_region: DEFB 0
g_reg:    DEFS 8
g_exits:  DEFB 0
g_side:   DEFB 0
g_x:      DEFB 0
g_y:      DEFB 0
g_h:      DEFB 0
g_w:      DEFB 0
g_t:      DEFB 0
g_r:      DEFB 0
gseed:    DEFW 1
rf_tile:  DEFB 0
rf_prot:  DEFB 0
rg_x0:    DEFB 0
item_tx:  DEFB 0
item_ty:  DEFB 0
pool_cx:  DEFB 0
pool_cy:  DEFB 0
gen_sp:   DEFS 8
