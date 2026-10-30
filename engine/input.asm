; ---------------------------------------------------------------- input.asm
; read_input -> A = IN_* bits (Kempston order: R L D U F), for ctrl_type:
;   0 keyboard  Q left, W right, R up, E down, T fire (Underwurlde layout)
;   1 Kempston  port $1F
;   2 Cursor    5 left, 6 down, 7 up, 8 right, 0 fire
;   3 Interface II (port 1)  6 left, 7 right, 8 down, 9 up, 0 fire
read_input:
        IF DEMO
        ld a,(demo_on)
        or a
        jp nz,demo_input
        ENDIF
        ld a,(ctrl_type)
        or a
        jr z,ri_kb
        dec a
        jr z,ri_kemp
        dec a
        jr z,ri_cur
        ; Interface II: $EFFE  b4=6 b3=7 b2=8 b1=9 b0=0
        ld a,$EF
        in a,($FE)
        cpl
        ld c,a
        ld b,0
        bit 4,c
        jr z,ri_s1
        set 1,b
ri_s1:  bit 3,c
        jr z,ri_s2
        set 0,b
ri_s2:  bit 2,c
        jr z,ri_s3
        set 2,b
ri_s3:  bit 1,c
        jr z,ri_s4
        set 3,b
ri_s4:  bit 0,c
        jr z,ri_s5
        set 4,b
ri_s5:  ld a,b
        ret
ri_kemp:
        in a,($1F)
        cp $FF                  ; floating bus / no interface
        jr nz,ri_k1
        xor a
        ret
ri_k1:  and $1F
        ret
ri_cur: ld a,$F7                ; 5 = b4
        in a,($FE)
        cpl
        ld b,0
        bit 4,a
        jr z,ri_c1
        set 1,b
ri_c1:  ld a,$EF                ; b4=6 down, b3=7 up, b2=8 right, b0=0 fire
        in a,($FE)
        cpl
        ld c,a
        bit 4,c
        jr z,ri_c2
        set 2,b
ri_c2:  bit 3,c
        jr z,ri_c3
        set 3,b
ri_c3:  bit 2,c
        jr z,ri_c4
        set 0,b
ri_c4:  bit 0,c
        jr z,ri_c5
        set 4,b
ri_c5:  ld a,b
        ret
ri_kb:  ld a,$FB                ; Q b0, W b1, E b2, R b3, T b4
        in a,($FE)
        cpl
        ld c,a
        ld b,0
        bit 0,c
        jr z,ri_b1
        set 1,b
ri_b1:  bit 1,c
        jr z,ri_b2
        set 0,b
ri_b2:  bit 2,c
        jr z,ri_b3
        set 2,b
ri_b3:  bit 3,c
        jr z,ri_b4
        set 3,b
ri_b4:  bit 4,c
        jr z,ri_b5
        set 4,b
ri_b5:  ld a,b
        ret

; any_key: NZ if any key is held
any_key:
        xor a
        in a,($FE)
        cpl
        and $1F
        ret

; wait_no_key / wait_key
wait_no_key:
        halt
        call any_key
        jr nz,wait_no_key
        ret
wait_key:
        halt
        call any_key
        jr z,wait_key
        ret

; check_pause: ENTER pauses, ENTER again resumes
check_pause:
        ld a,$BF
        in a,($FE)
        rra
        ret c
        call wait_no_key
cp_1:   halt
        ld a,$BF
        in a,($FE)
        rra
        jr c,cp_1
        call wait_no_key
        ret

ctrl_type: DEFB 0
