; ---------------------------------------------------------------- defs.asm
; Global constants for Mire Mare.
STACK_TOP   EQU $FDF0       ; stack grows down to ~$FB00
ISR_JP      EQU $FDFD       ; IM2 lands here (JP isr)
VEC_TABLE   EQU $FE00       ; 257 x $FD
MIRROR      EQU $E000       ; clean copy of the screen (bitmap+attrs) $E000-$FAFF
MOFS        EQU $A0         ; screen high byte + MOFS = mirror high byte
PLAY_TOP    EQU 16          ; first pixel row of the play area (2 HUD rows above)
F_SOLID     EQU 1
F_SLOW      EQU 2
F_SINK      EQU 4
F_ITEM      EQU 8
IN_RIGHT    EQU 1           ; input bits, Kempston order
IN_LEFT     EQU 2
IN_DOWN     EQU 4
IN_UP       EQU 8
IN_FIRE     EQU 16
PX_MAX      EQU 232         ; player x range 0..232 (24 px sprite)
PY_MAX      EQU 152         ; player y range 0..152 (play coords)
SINK_MAX    EQU 20          ; rows sunk before drowning
START_LIVES EQU 5
MAX_LIVES   EQU 7
; room_flags bits
RF_GOT      EQU 1           ; the room's item has been taken
RF_SEEN     EQU 2           ; visited
; day / night (in 25 Hz ticks)
DAY_LEN     EQU 6000        ; 4 minutes
NIGHT_LEN   EQU 3000        ; 2 minutes
; items (world.py ITEM kinds)
IT_LIGHT    EQU 1
IT_BIT      EQU 2
IT_REIN     EQU 3
IT_HEAD     EQU 4
IT_BUCKLE   EQU 5
IT_LANTERN  EQU 6
IT_KEY      EQU 7
IT_LEVER    EQU 8
IT_BUD      EQU 9
; power-ups (mire-blooms), in colour order
PU_WATER    EQU 0           ; cyan    no sinking
PU_SWIFT    EQU 1           ; yellow  double speed
PU_WARD     EQU 2           ; magenta invulnerable
PU_LIFE     EQU 3           ; green   extra life
PU_FEVER    EQU 4           ; red     reversed controls
PU_DROWSE   EQU 5           ; white   frozen
