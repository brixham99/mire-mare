; ---------------------------------------------------------------- jukebox.asm
; Sound-check build only (./build.sh sfx): plays every effect in turn with
; one second of silence between them, so a Fuse recording can be cut into
; one clip per effect.  The border shows the effect number while it plays.
jukebox:
        ld b,100
jb_0:   halt
        djnz jb_0
        ld hl,jb_tab
        ld c,1
jb_1:   ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,d
        or e
        jr z,jb_end
        push hl
        push bc
        ld a,c
        and 7
        out ($FE),a
        ld hl,jb_ret
        push hl
        ex de,hl
        jp (hl)
jb_ret: xor a
        out ($FE),a
        ld b,50
jb_w:   halt
        djnz jb_w
        pop bc
        inc c
        pop hl
        jr jb_1
jb_end: halt
        jr jb_end
jb_tune:
        ld hl,menu_tune
        jp play_tune
jb_tab: DEFW sfx_swing,sfx_hit,sfx_kill,sfx_pickup,sfx_quest,sfx_death
        DEFW sfx_squelch,sfx_hoof,sfx_neigh,sfx_ox,sfx_toll,sfx_dawn
        DEFW sfx_hag,sfx_clod,sfx_menu,jb_tune,0
