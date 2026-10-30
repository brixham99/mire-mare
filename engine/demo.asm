; ---------------------------------------------------------------- demo.asm
; DEMO / verification build only.  Inputs come from an RLE stream
; (packed by tools/pack_stream.py; format there) instead of the keyboard, so a run planned headless replays
; tick-for-tick in a real emulator.  Commands (input byte >= $80):
;   $80 room x y   warp (cheat)        $81  advance the clock to the next
;   $82 bits       give bridle pieces  $83  make Sabreman invulnerable
;   $FF            end of stream (input 0 afterwards)
; demo_on = 1 plays demo_data; 2 = live: the harness pokes demo_live.
demo_start:
        ld hl,demo_data+7       ; skip the 7-byte input table
        ld (demo_ptr),hl
        xor a
        ld (demo_cnt),a
        ld (demo_god),a
        ld a,(demo_data)
        cp $FE                  ; $FE = no stream: live mode
        ld a,1
        jr nz,ds_1
        inc a
ds_1:   ld (demo_on),a
        ret

demo_input:
        ld hl,(demo_reads)
        inc hl
        ld (demo_reads),hl
        call demo_god_tick
        ld a,(demo_on)
        cp 2
        jr z,di_live
        ld a,(demo_cnt)
        or a
        jr nz,di_have
        ld hl,(demo_ptr)
di_next:
        ld a,(hl)
        cp $FF
        jr z,di_zero
        inc hl
        cp $FE                  ; part A done: part B was moved to $5B00
        jr nz,di_n1
        ld hl,$5B00
        jr di_next
di_n1:  cp $E0
        jr c,di_short
        jr nz,di_cmd
        ld a,(hl)               ; $E0 i n: long run
        inc hl
        call di_val
        ld a,(hl)
        inc hl
        jr di_set
di_short:                       ; iii nnnnn
        ld b,a
        rlca
        rlca
        rlca
        and 7
        call di_val
        ld a,b
        and 31
di_set: ld (demo_ptr),hl
di_have:
        dec a
        ld (demo_cnt),a
        ld a,(demo_cur)
        ret
di_val: push hl                 ; demo_cur = table[A]
        ld hl,demo_data
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld a,(hl)
        ld (demo_cur),a
        pop hl
        ret
di_zero:
        xor a
        ret
di_cmd: sub $E1-$80             ; $E1..$E4 -> command $80..$83
        ld de,demo_ptr
        call demo_cmd
        xor a
        ret
; live: demo_live holds the input; a command is (demo_live) >= $80 with
; its arguments in demo_args.  The harness clears demo_live after a command.
di_live:
        ld a,(demo_live)
        cp $80
        ret c
        ld b,a
        xor a
        ld (demo_live),a        ; clear first: a warp's room load spans frames
        ld a,b
        ld hl,demo_args
        call demo_cmd
        xor a
        ret

; demo_cmd: A = command, HL -> arguments.  For the stream, DE = demo_ptr to update.
demo_cmd:
        cp $80
        jr nz,dc_1
        ld a,(hl)
        inc hl
        ld (dc_room),a
        ld a,(hl)
        inc hl
        ld (px),a
        ld (prev_px),a
        ld a,(hl)
        inc hl
        ld (py),a
        ld (prev_py),a
        call dc_save
        ld a,(dc_room)
        jp change_room
dc_1:   cp $81
        jr nz,dc_2
        call dc_save
        ld hl,1
        ld (clock),hl
        ret
dc_2:   cp $82
        jr nz,dc_3
        ld a,(hl)
        inc hl
        call dc_save
        ld hl,bridle
        or (hl)
        ld (hl),a
        ld a,1
        ld (hud_dirty),a
        ret
dc_3:   call dc_save
        ld a,1
        ld (demo_god),a
        ret
dc_save:
        ld a,(demo_on)
        cp 1
        ret nz
        ld (demo_ptr),hl
        ret

demo_god_tick:
        ld a,(demo_god)
        or a
        ret z
        ld a,4
        ld (pinv),a
        ret

demo_on:   DEFB 0
demo_reads: DEFW 0
demo_cnt:  DEFB 0
demo_cur:  DEFB 0
demo_god:  DEFB 0
demo_ptr:  DEFW 0
demo_live: DEFB 0
demo_args: DEFS 4
dc_room:   DEFB 0
