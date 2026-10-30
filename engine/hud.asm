; ---------------------------------------------------------------- hud.asm
; Row 0: SCORE 000000   lives          HI 000000
; Row 1: GEMS 00   BRIDLE ....        MIRE ....
CH_LIFE  EQU 128
CH_PIECE EQU 129
CH_BLOCK EQU 130
CH_EMPTY EQU 131
CH_FRH   EQU 132
CH_FRV   EQU 133
CH_FRC   EQU 134
CH_SUN   EQU 135
CH_MOON  EQU 136
CH_LANT  EQU 137
CH_KEY   EQU 138

hud_init:
        ld d,0
        ld e,0
        ld b,2
        ld c,32
        xor a
        call clear_box
        ld hl,hud_labels
        call print_str
        ld a,$FF
        ld (hud_last_sink),a
        jp hud_all

hud_labels:
        DEFB 1,0,0,2,$45,"SCORE"
        DEFB 1,0,22,2,$45,"HI"
        DEFB 1,1,0,2,$45,"LITE"
        DEFB 1,1,9,2,$45,"BRIDLE"
        DEFB 1,1,22,2,$45,"MIRE",0

hud_all:
        call hud_score
        call hud_hi
        call hud_lives
        call hud_gems
        call hud_bridle
        call hud_clock
        jp hud_mire

; hud_update: redraw only what changed this tick
hud_update:
        ld a,(hud_dirty)
        or a
        jr z,hu_1
        xor a
        ld (hud_dirty),a
        call hud_score
        call hud_lives
        call hud_gems
        call hud_bridle
hu_1:   ld a,(psink)
        ld hl,hud_last_sink
        cp (hl)
        ret z
        jp hud_mire

hud_score:
        ld a,0
        ld (pr_row),a
        ld a,6
        ld (pr_col),a
        ld a,$46
        ld (pr_attr),a
        ld hl,score
        ld b,6
hs_1:   ld a,(hl)
        call print_char
        inc hl
        djnz hs_1
        ret
hud_hi:
        xor a
        ld (pr_row),a
        ld a,25
        ld (pr_col),a
        ld a,$46
        ld (pr_attr),a
        ld hl,hiscore
        ld b,6
hh_1:   ld a,(hl)
        call print_char
        inc hl
        djnz hh_1
        ret
hud_lives:
        xor a
        ld (pr_row),a
        ld a,13
        ld (pr_col),a
        ld a,$47
        ld (pr_attr),a
        ld a,(lives)
        ld c,a
        ld b,0
hl_1:   ld a,b
        cp c
        ld a,CH_LIFE
        jr c,hl_2
        ld a,' '
hl_2:   call print_char
        inc b
        ld a,b
        cp MAX_LIVES
        jr nz,hl_1
        ret
hud_gems:
        ld a,1
        ld (pr_row),a
        ld a,5
        ld (pr_col),a
        ld a,$45
        ld (pr_attr),a
        ld a,(gems)
        ld b,'0'
hg_1:   cp 10
        jr c,hg_2
        sub 10
        inc b
        jr hg_1
hg_2:   push af
        ld a,b
        call print_char
        pop af
        add a,'0'
        jp print_char
hud_bridle:
        ld a,1
        ld (pr_row),a
        ld a,16
        ld (pr_col),a
        ld a,(bridle)
        ld c,a
        ld b,4
hb_1:   ld a,$41                ; dim slot
        rr c
        jr nc,hb_2
        ld a,$46                ; found: bright yellow
hb_2:   ld (pr_attr),a
        ld a,CH_PIECE
        call print_char
        djnz hb_1
        ; lantern and key
        ld a,(has_lantern)
        or a
        ld a,$46
        jr nz,hb_3
        xor a
hb_3:   ld (pr_attr),a
        ld a,CH_LANT
        call print_char
        ld a,(has_key)
        or a
        ld a,$45
        jr nz,hb_4
        xor a
hb_4:   ld (pr_attr),a
        ld a,CH_KEY
        jp print_char
; mire meter: 4 cells fill as Sabreman sinks
hud_mire:
        ld a,(psink)
        ld (hud_last_sink),a
        ld b,0
hm_0:   cp 5
        jr c,hm_00
        sub 5
        inc b
        jr hm_0
hm_00:  or a
        jr z,hm_01
        inc b                   ; any part-cell counts as one
hm_01:  ld a,1
        ld (pr_row),a
        ld a,27
        ld (pr_col),a
        ld c,4
hm_1:   ld a,b
        or a
        jr z,hm_2
        dec b
        ld a,$42                ; red-filled block
        ld (pr_attr),a
        ld a,CH_BLOCK
        jr hm_3
hm_2:   ld a,$45
        ld (pr_attr),a
        ld a,CH_EMPTY
hm_3:   call print_char
        dec c
        jr nz,hm_1
        ret

hud_dirty:     DEFB 0
hud_last_sink: DEFB 0
