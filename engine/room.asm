; ---------------------------------------------------------------- room.asm
; Rooms are 16x11 tiles of 16x16 px, drawn at char rows 2-23.
; room_load: A = room number.  Generates the room (roomgen.asm), applies the
; day/night and quest-state tile swaps, removes a taken item, draws it,
; snapshots the clean screen into the mirror and spawns the room's creatures.
room_load:
        ld (cur_room),a
        call room_gen
        call room_post
        ; visited
        ld a,(cur_room)
        ld hl,room_flags
        call add_a_hl
        set 1,(hl)
        call room_draw
        ; no sprite is on screen any more
        xor a
        ld (rec_player),a
        ld (rec_en),a
        ld (rec_en+9),a
        ld (rec_en+18),a
        ld (rec_mare),a
        call enemies_spawn
        call cache_build
        call bud_find
        jp mare_room_enter

; room_draw: all tiles to the screen, then copy to the mirror
room_draw:
        xor a
        ld (dt_ofs),a
        ld hl,roombuf
        ld c,0
rd_5:   ld b,0
rd_6:   ld a,(hl)
        push hl
        call draw_tile
        pop hl
        inc hl
        inc b
        ld a,b
        cp 16
        jr nz,rd_6
        inc c
        ld a,c
        cp 11
        jr nz,rd_5
        ld hl,$4000
        ld de,MIRROR
        ld bc,6912
        ldir
        ret

; room_post: tile swaps for night, lantern, key, causeway; taken item
room_post:
        ld hl,roombuf
        ld b,176
rp_1:   ld a,(hl)
        ld c,a
        ld a,(night)
        or a
        jr z,rp_day
        ld a,c
        cp TILE_NIGHTLILY
        jr z,rp_lily
        cp TILE_SHALLOW
        jr nz,rp_n2
        ld (hl),TILE_BOG        ; the bog rises by night
        jr rp_next
rp_n2:  cp TILE_CAUSEWAYSUNK
        jr nz,rp_n3
        ld a,(causeway_up)
        or a
        jr nz,rp_cw
rp_lily:
        ld (hl),TILE_LILYPAD
        jr rp_next
rp_n3:  cp TILE_SPIRITDOOR
        jr nz,rp_com
        ld a,(has_lantern)
        or a
        jr z,rp_next
        ld (hl),TILE_FLAGSTONE
        jr rp_next
rp_day: ld a,c
        cp TILE_CAUSEWAYSUNK
        jr nz,rp_com
        ld a,(causeway_up)
        or a
        jr z,rp_next
rp_cw:  ld (hl),TILE_CAUSEWAY
        jr rp_next
rp_com: ld a,c
        cp TILE_CRYPTDOOR
        jr nz,rp_next
        ld a,(has_key)
        or a
        jr z,rp_next
        ld (hl),TILE_FLAGSTONE
rp_next:
        inc hl
        djnz rp_1
        ; taken item?
        ld a,(item_tx)
        cp $FF
        ret z
        ld a,(cur_room)
        ld hl,room_flags
        call add_a_hl
        bit 0,(hl)
        ret z
        ld a,(item_tx)
        ld b,a
        ld a,(item_ty)
        ld c,a
        call cell_hl
        call item_under
        ld (hl),a
        ld a,$FF
        ld (item_tx),a
        ret

; item_under -> A = tile left behind when the item goes (bog if it sat in a pool)
item_under:
        ld a,(g_desc+3)
        and 16
        ld a,TILE_FLOOR
        ret z
        ld a,(night)
        or a
        ld a,TILE_BOG
        ret nz
        ld a,(pool_cx)
        cp $FF
        ld a,TILE_FLOOR
        ret z
        ld a,TILE_BOG
        ret

; draw_tile: B = tx, C = ty, A = tile.  Writes to screen + (dt_ofs) high-byte
; offset (0 = screen, MOFS = mirror).  Attributes lose BRIGHT at night.
; Preserves BC.
draw_tile:
        push bc
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ld de,tile_gfx
        add hl,de
        ex de,hl                ; DE = tile data
        ld a,c
        add a,a
        add a,2
        ld (dt_row),a
        ld a,b
        add a,a
        ld (dt_col),a
        call dt_half
        ld hl,dt_row
        inc (hl)
        call dt_half
        ld hl,dt_row
        dec (hl)
        ; attributes
        push de
        ld a,(dt_row)
        ld d,a
        ld a,(dt_col)
        ld e,a
        call attr_addr
        ld a,(dt_ofs)
        add a,h
        ld h,a
        pop de
        ld bc,(dim_mask)        ; C = mask
        ld a,(de)
        and c
        ld (hl),a
        inc de
        inc l
        ld a,(de)
        and c
        ld (hl),a
        inc de
        ld a,l
        add a,31
        ld l,a
        jr nc,dt_a
        inc h
dt_a:   ld a,(de)
        and c
        ld (hl),a
        inc de
        inc l
        ld a,(de)
        and c
        ld (hl),a
        pop bc
        ret
dt_half:
        push de
        ld a,(dt_row)
        ld d,a
        ld a,(dt_col)
        ld e,a
        call char_addr
        ld a,(dt_ofs)
        add a,h
        ld h,a
        pop de
        ld b,8
dh_1:   ld a,(de)
        ld (hl),a
        inc de
        inc l
        ld a,(de)
        ld (hl),a
        inc de
        dec l
        inc h
        djnz dh_1
        ret

; redraw_tile: B = tx, C = ty: redraw roombuf tile on screen and in mirror
redraw_tile:
        call cell_hl
        ld a,(hl)
        push af
        xor a
        ld (dt_ofs),a
        pop af
        push af
        call draw_tile
        ld a,MOFS
        ld (dt_ofs),a
        pop af
        call draw_tile
        xor a
        ld (dt_ofs),a
        ret

; tile_at: B = x, C = y (play coords) -> A = tile flags, HL -> roombuf entry.
; Preserves BC.
tile_at:
        ld a,c
        cp 176
        jr nc,ta_out
        and $F0
        ld l,a
        ld a,b
        rrca
        rrca
        rrca
        rrca
        and $0F
        or l
        ld l,a
        ld h,0
        ld de,roombuf
        add hl,de
        ld a,(hl)
        push hl
        ld hl,tile_flags
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld a,(hl)
        pop hl
        ret
ta_out: ld hl,roombuf
        ld a,F_SOLID
        ret

; set_tile_attr: B = tx, C = ty, A = attr -> the tile's 4 cells, screen + mirror
set_tile_attr:
        push bc
        ld (sta_a),a
        ld a,c
        add a,a
        add a,2
        ld d,a
        ld a,b
        add a,a
        ld e,a
        call attr_addr
        ld a,(sta_a)
        ld (hl),a
        inc l
        ld (hl),a
        ld de,31
        add hl,de
        ld (hl),a
        inc l
        ld (hl),a
        ld de,MOFS*256-33
        add hl,de
        ld (hl),a
        inc l
        ld (hl),a
        ld de,31
        add hl,de
        ld (hl),a
        inc l
        ld (hl),a
        pop bc
        ret
sta_a:     DEFB 0

cur_room:  DEFB 0
dt_row:    DEFB 0
dt_col:    DEFB 0
dt_ofs:    DEFB 0
dim_mask:  DEFB $FF         ; $BF at night (BRIGHT off)
roombuf:   DEFS 176
room_flags: DEFS NUM_ROOMS
