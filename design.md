# MIRE MARE — Game Design (Phase 2)

*An Ultimate Play The Game–style flip-screen adventure for the 48K ZX Spectrum, packaged as a 1984-85 black big box.*
Status: design proposal plus a playable vertical slice (region 1, The Sedge Fen). The slice is in `build/miremare.tap`.

All story, map, creature and item ideas here are new. They follow Ultimate's *conventions*: a terse inlay legend, flip screens on black, collectable pieces, a percentage and rating screen, and an Ultimate-style menu. They deliberately do **not** reuse the fan remake's volcano, three gems or wulf-statue exit, or the Retro Gamer mock-ups' lava lake, Mount Sol and horizontal scrolling.

---

## 1. Premise

> *Sabreman sleeps no more. Since he won the Pentagram's power and drove the Lord of Underwurlde back below, something rides him through the night: hoof-beats in the dark, a weight upon the chest. Every night it drags him a little further from waking, and the dream always ends at the same place: the drowned fen of MIRE MARE, where a grey mare with burning eyes waits on an island in the black Mere.*
>
> *The fen-folk know the old cure. A Night Mare can be ridden only if it is bridled. Find the four pieces of the Mare's Bridle — the BIT, the REIN, the HEADSTALL and the BUCKLE — before the dark takes you, and the Mare that rides you shall be ridden.*

- **Story tone:** this is the end of the saga. The adventure the wulf, the Pentagram and Underwurlde led to is Sabreman's own nightmare.
- **Folklore root:** the *mare* is the night spirit that "rides" sleepers, which is where "nightmare" comes from. Bridling it was the folk remedy.
- **The title** is a pun on mire and (night)mare, as Ultimate intended.

## 2. The world

There are **160 screens**: a **16 × 10 grid** of flip screens. Each screen is 16 × 11 tiles of 16 × 16 px (256 × 176 px). Above them sit 2 character rows of HUD. Exits are gaps in each screen's wall of scenery, as in Sabre Wulf. There is no scrolling anywhere.

```
      0 1 2 3 4 5 6 7 8 9 A B C D E F
  0   W W W W W W a a a a a a P P P P     W = Gloaming Wood   (30)
  1   W W W W W W a a A a a a P P P P     a = Sunken Abbey    (26)  A = crypt stairs
  2   W W W W W a a a a a a a P P P P     S = Sedge Fen       (36)  * = start screen
  3   W W W W # a a a a a # # P P P P     P = Peat Hags       (40)
  4   S S S S # m m m m m m # P P P P     m = The Mere        (24)
  5   S S S S m m m I I m m m P P P P     I = Mare's Isle      (4)  guardian
  6   S S S * m m m I I m m m P P P P     # = thorn / deep water (impassable)
  7   S S S S S m m m m m m P P P P P
  8   S S S S S S S m m S S P P P P P
  9   S S S S S S S S S S S P P P P P
```

- **Rule:** you can enter the Mere screens only via lily paths, which surface at night, or via the abbey causeway, which is opened from the crypt.
- **Region order:** Fen → Wood → Abbey → Hags, then the Isle. The regions are interconnected, so the player can attempt them in other orders.

### Regions and marsh mechanics

| Region | Palette (ink on black) | Terrain hazard | Bridle piece | Local foes |
|---|---|---|---|---|
| **Sedge Fen** (slice) | yellow reeds, green ferns, cyan water | shallow mire (½ speed), deep bog (sinks) | **Bit** | wisp, toad, adder |
| **Gloaming Wood** | green/white dead trees, magenta blooms | root snags (stop you for 1 s), fog cells that hide sprites | **Rein** | boggart, heron, wisp |
| **Sunken Abbey** | white stone, blue flood, red glass | rising water (cells flood on a timer), crypt doors | **Headstall** | drowned monk, leech |
| **Peat Hags** | red/yellow peat banks, black water | peat cuttings: drops that send you back a screen; deep bog | **Buckle** | bog-body, Mire Ox |
| **The Mere** | blue/cyan, lilies white | open water (drowning), night-only lily paths | — | night hags, the Night Mare |

**Mire rules:**

- **Shallow mire (`~`)** halves your speed.
- **Deep bog (`=`)** sinks you one pixel every 4 ticks. The sprite sinks into the cell, and the HUD **MIRE** meter fills.
- At **20 px** sunk you drown and lose a life.
- Standing on firm ground, a lily pad or a tussock lets you climb out at 1 px per tick.
- Deep bog is crossable for 3–4 tiles if you keep moving, so short bog crossings are risk/reward shortcuts.

## 3. Day and night — the "mare" phase

A **sun/moon clock** sits in the HUD. In the slice it is replaced by the MIRE meter.

- **Cycle:** a full day is about 6 minutes, with **4 min day and 2 min night**. Nightfall is signalled by a two-note toll and a border flicker.
- **What night changes:**
  - **Colour:** every tile ink loses BRIGHT, so the world visibly dims. This is a single pass over the tile attribute table at screen flip, at zero cost.
  - **Bog:** it rises. Shallow mire tiles count as deep bog.
  - **Enemies:** wisps become fast and aggressive. **Bog-bodies** climb out of bog tiles, and **night hags** blink between screen edges.
  - **The Night Mare ROAMS the fen at night as an unkillable hunter** (decided by Nathan). Every ~3.6 s she moves one screen toward Sabreman. Hoof-beats warn you: slow beats when she is 2 screens away, fast when 1 away, a gallop when she bursts in. In your screen she gallops across, drifting toward your row; her touch costs a life, then she bolts to a neighbouring screen and rests briefly. A sabre hit without the full bridle only makes her neigh and flee. At dawn she returns to her home screen on Mare's Isle.
  - **Night-only routes:** lily paths surface on the Mere (the only way to reach Mare's Isle besides the causeway), and **spirit doors** in the Abbey open.
- **Trade-off:** night is when progress is possible, and when the fen is most deadly.

## 4. Creatures

| # | Creature | Where | Behaviour | Kill |
|---|---|---|---|---|
| 1 | Will-o'-wisp | everywhere | drifts toward you, floats over scenery | sabre, 100 |
| 2 | Marsh toad | Fen | hops in bursts, random turns | sabre, 100 |
| 3 | Fen adder | Fen, Hags | fast horizontal patrol, doubles speed when level with you | sabre, 100 |
| 4 | Grey heron | Fen, Mere | stands still, then lunges in a straight line | sabre, 200 |
| 5 | Leech | Abbey water | clings, slowing you until you swing | sabre, 50 |
| 6 | Boggart | Wood | throws clods, takes two hits | sabre ×2, 300 |
| 7 | Drowned monk | Abbey | follows walls, rises from flooded cells | sabre, 200 |
| 8 | Bog-body | Hags, night | rises from bog tiles, slow and relentless | sabre ×3, 400 |
| 9 | Mire Ox | Hags | huge 32×24 charger, can't be killed, sabre staggers it | — |
| 10 | **The Night Mare** (guardian) | Isle, and roaming at night | gallops in long arcs, deadly to touch | bridle only |

**Spawning:** enemies materialise in a white sparkle at the room's spawn points, as the slice does. A dead enemy respawns after about 5 seconds, so the sabre buys time rather than clearing rooms.

## 5. Items and power-ups

- **Marsh-lights** are collectables, 10 per region and 40 in total, worth 500 each. They feed the percentage and the rating.
- **The Mare's Bridle** comes in four pieces: Bit, Rein, Headstall and Buckle, one guarded deep in each region. Each pickup shows a rhyme box, as the slice does:
  *"THE BIT IS FOUND / ONE PIECE OF FOUR / BRIDLE THE MARE / TO DREAM NO MORE"*
- **Mire-blooms** are an homage to Sabre Wulf's orchids, with different mechanics. Buds grow on certain tussocks and **open only while Sabreman stands on a neighbouring tile**, cycling colour about once per second. Walk onto the bloom to take the current effect:
  - **cyan** — Water-walk: no sinking for 10 s
  - **yellow** — Swift-foot: double speed
  - **magenta** — Ward: invulnerable for 8 s
  - **green** — Extra life (rare)
  - **red** — Bog-fever: controls reversed
  - **white** — Drowse: frozen for 2 s
- **Lantern and Abbey key** are progression items. The lantern reveals spirit doors; the key opens the crypt that lowers the abbey causeway.

**Controls decision (Nathan):** the sabre swings LEFT/RIGHT only; up/down just walk.

## 6. Guardian and endings

- **Mare's Isle** (4 screens) can be reached at night across the lily paths.
- **Without all four bridle pieces:** the Mare's touch costs a life (she then flees); a sabre hit just drives her off.
- **With the full bridle:** a sabre hit "bridles" her. The screen flashes, and the Mare kneels.
- **Ending A — "THE MARE IS BRIDLED":** Sabreman rides out of the fen at dawn. The percentage and rating screen follows.
- **Ending B — 100%** (every marsh-light, every piece, every screen visited): an extra Ultimate-style closing scroll in place of the usual "next adventure" teaser:
  *"SABREMAN HAS RIDDEN HIS NIGHTMARE HOME. THE SAGA IS ENDED. SLEEP WELL."*
- **Game over:** shows **QUEST COMPLETED nn%** and **OVERALL RATING**. This is implemented in the slice.
  - **Ranks:** BOG TROTTER (0–24), FEN WALKER (25–49), MIRE STRIDER (50–74), MARSH LORD (75–99), ULTIMATE (100).
  - **Full game percentage:**
    - each screen visited: 0.25% (40 total)
    - each marsh-light: 0.75% (30 total)
    - each bridle piece: 5% (20 total)
    - the bridled Mare: 10%
  - In the slice the percentage covers its 11 items (10 lights and 1 piece).

## 7. HUD, menu and controls

```
SCORE 000500 ☠☠☠☠☠        HI 010000      row 0
GEMS 01  BRIDLE ♥♥♥♥      MIRE ▢▢▢▢      row 1   (full game: sun/moon clock replaces MIRE when dry)
```

- **Lives** use a small Sabreman-head icon. The four bridle slots light **bright yellow** as pieces are found.
- **The menu** has an Ultimate-style double frame (bright knotwork and a red inner rule), the title in 2× lettering, and the ACG copyright line. The selected option is shown in bright yellow. The menu plays the title tune.
  - **1** Keyboard
  - **2** Kempston joystick
  - **3** Cursor joystick (5 6 7 8, 0 = fire)
  - **4** Interface II (port 1: 6 7 8 9, 0 = fire)
  - **0** Start game

| Action | Keyboard | Kempston | Cursor | Interface II |
|---|---|---|---|---|
| Left | Q | left | 5 | 6 |
| Right | W | right | 8 | 7 |
| Up | R | up | 7 | 9 |
| Down | E | down | 6 | 8 |
| Sabre | T | fire | 0 | 0 |
| Pause | ENTER | — | ENTER | ENTER |

The keyboard layout (QWERT on one row) follows Ultimate's own Underwurlde inlay.

## 8. Sound (beeper)

- **Title tune:** about 4 s, a mournful two-octave jig. Any key skips it.
- **In-game effects, all short blocking loops of under 40 ms** so they never drop a game tick:
  - sabre swish (rising sweep)
  - marsh-light pickup (rising arpeggio)
  - bridle fanfare
  - enemy burst (noise)
  - squelch every 8th step in mire
  - death (falling sweep plus noise)
- **Full game additions:** hoof-beats (the Night Mare's approach), the nightfall toll and the bloom chime.
- **No in-game music,** in keeping with Ultimate's 1984-85 titles.

## 9. Graphics

- **Colour rule** (the reason there is no attribute clash):
  - Paper is **always black**. Every 8 × 8 cell holds one ink plus black.
  - **Sabreman has no colour of his own.** He takes the ink of the cell he's in: white on floor, cyan when wading, blue in the bog.
  - **Enemies paint their own ink, but only into empty-floor cells.** Scenery cells keep their colour.
  - So no cell ever needs more than 2 colours. This is the Sabre Wulf approach, made strict.
- **Sprites:**
  - Sabreman is 24 × 24 with a black keyline (mask) so he reads cleanly over scenery. He has 4 directions × 2 walk frames, plus left and right sabre-swing frames.
  - Enemies are 16 × 16 with 2 frames each.
- **Tiles:** 16 × 16 each, with 4 attributes per tile and one ink per quarter. Each region has a set of 16 tiles.
- **Art pipeline:**
  - Sprites, tiles, UDGs and the map are authored as **text art** (`art/*.txt`).
  - `tools/gfx.py` (graphics) and `tools/world.py` (the generated 160-screen map, checked by `tools/validate_world.py` and `tools/progression.py`) convert them to assembler. They add the keyline, generate the mirrored frames and the pre-shifts, and validate exits.
  - The tools also write PNG previews (`build/sprites_preview.png`, `build/map_preview.png`).

### Loading screen style (from Nathan's references)

The style comes from Nathan's four references: Underwurlde, Cyberun, Sabre Wulf and Knight Lore, stored in `refs/loading_screens/`. The common traits are:

1. a **hand-lettered, stylised title**
2. a **thick, bright decorative frame**: Celtic interlace or a bevelled geometric border
3. an **illustrative character or scene**, usually on a coloured or black ground
4. the **ULTIMATE / PLAY THE GAME badge** bottom-right in a framed box: green chrome "ULTIMATE", cyan "PLAY THE GAME", black box with a white outline

**The Mire Mare SCREEN$ (placeholder, generated by `tools/mkscr.py`):**

- **Frame:** a bright cyan-on-blue two-strand interlace frame, 2 cells thick, with roundel corners.
- **Title:** "Mire Mare" in gothic hand-lettering, white with a magenta drop shadow.
- **Scene:** a starry night with the **Night Mare's head silhouetted in a yellow moon**, the moon's reflection on the Mere, reeds and bulrushes, a wisp, and Sabreman on a tussock.
- **Badge:** bottom-right.
- **Format:** a true 6912-byte screen. Every cell is quantised to one ink, one paper and one BRIGHT bit.
- **Next phase:** this will be replaced by hand-pixelled art in the packaging and artwork phase.

## 10. Technical plan (implemented in the slice)

- **Memory map (48K):**
  - 0x5B00–0x7FFF — BASIC/loader (full game: code ORG moves to 0x6000)
  - 0x8000–0xDFFF — code and data, 24K (slice uses 0x8000–0xC960, 18.8K)
  - 0xE000–0xFAFF — **screen mirror**: a clean copy of the room (bitmap and attributes), 6912 bytes
  - 0xFB00–0xFDF0 — stack
  - 0xFDFD — `JP isr`
  - 0xFE00–0xFF00 — IM2 vector table (257 × 0xFD)
- **Frame timing:**
  - The IM2 interrupt only counts frames. The main loop runs at a **locked 25 Hz**: halt, then wait until 2 frames have passed.
  - Measured: a normal game tick costs **17–34k T-states**, at most about 50% of one 69,888 T frame. There is plenty of headroom for the full game's 3 enemies, night logic and blooms.
  - A screen flip (decompress, draw 176 tiles, ldir to the mirror) takes about 8 frames (0.16 s).
- **Sprite routine:**
  - Masked sprites are drawn with `(screen AND mask) OR ink`, using interleaved mask/ink bytes.
  - They are **pre-shifted at 2-px steps**: 4 copies (x is always even), each one byte wider than the sprite.
  - Erase is a rectangle copy from the mirror, so there is no XOR flicker and no background save buffers.
  - Per-tick order: erase all, draw enemies, draw Sabreman (always on top). Each draw writes a 9-byte record (screen address, width, rows, attribute rectangle) that the next erase uses.
  - Moving ink pixels are drawn after the interrupt, early in the frame, so tearing is minimal.
- **Attributes:** enemies recolour only floor cells (checked against the mirror's attributes). The erase restores the attribute rectangle from the mirror.
- **No IX/IY:** all per-enemy state is copied to a scratch block (`ldir`), processed and copied back. This is fast on the Z80, and it lets the game run in the project's headless test core.
- **Rooms:**
  - Room data is RLE: a literal tile, or 0x80|n followed by a tile.
  - A room header holds the RLE pointer, 3 enemy spawns (type, x, y) and an optional start position.
  - Collected items are stored as per-room bit flags, and are removed from the decompressed room buffer at load.
  - Slice: 12 rooms in 1,315 bytes.
- **Full-game compression:** 160 RLE rooms would need about 18K, so the full game uses **prefab rooms**:
  - Each room is a 16-byte record: a border template id (exit mask plus region) and up to 6 placed "clumps" (prefab id, x, y), plus enemies and items.
  - It is expanded into the same 176-byte buffer, so the rest of the engine is unchanged.
  - Clumps are small RLE blocks shared across a region.
  - Estimate: **160 × 16 bytes plus about 3K of prefabs ≈ 5.5K**.
- **Enemy graphics, full game:** stored unshifted, with 4 shifts generated into a per-room cache when you enter a screen. Only 3 types are ever live at once.

### 48K memory budget (full game)

| Item | Slice (actual) | Full game (estimate) |
|---|---|---|
| Engine code (+ vars) | 5.0K | 9–10K (night cycle, blooms, guardian, 10 enemy AIs, endings) |
| Sabreman sprites (pre-shifted) | 7.7K* | 4.6K (6 frames + runtime mirroring) |
| Enemy sprites | 3.1K* (pre-shifted) | 1.6K unshifted (≈25 frames) + 2.3K shift cache |
| Tiles (36 B each) | 0.6K (16) | 2.9K (5 × 16, with shared tiles) |
| Map | 1.3K (12 rooms, RLE) | 5.5K (160 prefab rooms) |
| Font, UDGs, text, tune | 1.1K | 2.5K (custom font, rhymes, ending scroll) |
| **Total** | **18.8K** | **≈ 29–31K** |

\* The slice pre-shifts everything for simplicity: 10.9K of sprites in total.

**Available:** 0x6000–0xDFFF gives 32K below the mirror, so the full game fits with about 1–3K to spare. If it gets tight, the fallbacks are:

- drop the mirror's attribute copy and rebuild attributes from the room (saves 768 bytes)
- generate the left-facing Sabreman frames at runtime

## 11. As built (Phase 3) — differences from the plan above

- **Map:** 160 screens (16×10) are *generated* on the Z80 by `room_gen` from a compact per-room descriptor (region, exits, item, pool, clump seed, enemies, night/lily/door/crypt/causeway flags) produced by `tools/world.py`. `tools/validate_world.py` re-runs the Z80 generator for every room and checks exits, reachability of items, spawns and the start: 160/160 valid. Tiles are shared across regions with per-region colouring rather than 5 separate sets.
- **Night:** tile swaps at room load (night lilies → lily pads, shallow → bog, sunk causeway → lily, spirit doors → floor with the lantern); BRIGHT is masked off; a moon replaces the sun in the HUD; nightfall tolls, dawn chimes. If dawn catches Sabreman with no dry tile in reach he gets a short water-walk grace.
- **Progression:** lantern (Wood) opens spirit doors at night → Abbey sanctum (Headstall); key (Hags) opens crypt doors → lever raises the causeway to the Isle by day; lily paths reach the Isle at night.
- **Enemy graphics:** stored unshifted; the types present are pre-shifted into a 3K cache at room entry. The Mare (32×24) uses a runtime shifter.
- **Items:** 40 marsh-lights, 12 mire-bloom buds, 4 bridle pieces, lantern, key, lever. Pieces/lantern/key/lever show a message box; all four pieces add a "bridle whole" verse.
- **Percentage** (implemented): rooms seen/4 + lights×3/4 + pieces×5 + Mare×10 (=100). Ending B (100%) adds the verse "THE FEN IS WHOLE AGAIN".
- **Not built in Phase 3:** night hags, boggart clod-throwing, wisps speeding up at night, the 100% closing scroll text (all added in Phase 4, below).
- **Verification build:** `DEMO EQU 1` adds a stream player with cheat commands (warp, clock jump, give pieces, god mode); `tools/bot.py` records a route, the stream is embedded, and Fuse replays it on the real ROM.

### 11a. Phase 4 additions and balance (normal play, no god mode)

- **Night hags** (type 9, the Mere by night only), **boggart clods** (lobbed when level; a clod that lands costs a life, the sabre bats one away), **wisps quicken at night** (≈1.5×), **the 100% saga scroll**, and the **Night Mare drawn in her own white cells** on the Mere/lily pads at night (no attribute clash).
- **Fairness fixes found by the no-god walker bot** (`tools/walker.py`, which plays with 0.24–0.48 s of look-ahead):
  - the sabre now reaches dy<20 (was 14, *inside* the body-hit band of 15): a creature closing straight up or down could never be cut down before;
  - herons rear for 10 ticks before a lunge, and lunge at 3 px/tick (was instant, 4 px/tick);
  - the bog ox paws and bellows for 10 ticks before it charges (was instant);
  - a struck creature is knocked back 12 px; a struck boggart stops its charge and rests;
  - after a death the screen's creatures fall back to their lairs and re-form (1 s + sparkle), so one death is not followed by another.
- Unchanged after testing: day 4 min / night 2 min, 150-tick (6 s) respawn, 3 creatures per screen, bog drain 20 rows, Mare step 90, 5 lives (max 7).
- **Sound check build** `./build.sh sfx` plays all 16 effects; `tools/audio_check.py` analyses the Fuse WAV (see PROGRESS.md).

## 12. Remaining work for the full game (original estimate)

| Work | Size |
|---|---|
| Prefab map system and map editor/validator, plus designing 160 screens | large |
| Day/night cycle, night bog rules, lily paths and spirit doors | medium |
| 7 more enemy AIs (heron, leech, boggart, monk, bog-body, Mire Ox, hags) and the roaming Night Mare | large |
| Mire-blooms, lantern, key, causeway and crypt logic | medium |
| Guardian fight, endings, full percentage and rating, hi-score | small–medium |
| Art: 4 more tile sets, enemy frames, final Sabreman, custom font, final loading screen | large (art phase) |
| Sound: hooves, toll and blooms; final title tune | small |
| Balancing and play-testing in Fuse plus the headless suite; tape mastering | medium |

Roughly **5–8 more working sessions** of this size to reach a complete, balanced 160-screen game, with art and packaging on top.
