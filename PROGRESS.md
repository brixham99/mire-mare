# Mire Mare - progress notes (Phase 3)

## State at 14:20 Europe/London, 30 Oct 2026
- Full 160-screen map, day/night, roaming Mare, 9 enemies, items, both endings, rating are in.
- Builds: `./build.sh` -> build/miremare.tap (normal) + build/miremare_live.bin (cheat live-mode, for bot/tests)
  + runs tools/test_game.py. `./build.sh demo` -> build/miremare_demo.tap with build/demo_stream.asm embedded.
- Verification pipeline:
  1. `python3 tools/bot.py` (live build) plays the cheat route, writes build/demo_stream.asm + build/bot_events.json
  2. `./build.sh demo`; `python3 tools/replay_check.py` (headless replay must reach game_won)
  3. `python3 tools/fuse_demo.py 125` - real ROM in Fuse, sound on (SDL disk driver), --movie-start build/fuse_demo.fmf
     (NB: use --no-fastload; fastload broke the movie). The fuse_live_*.png shots after ~10 s all show the
     menu because the demo finishes fast and returns to the menu - NOT a hang.
  4. `fmfconv -y -w --sound-only -i build/fuse_demo.fmf -s build/fuse_demo.wav`; `fmfconv -y -G -i ... -o build/fmf/f.png`;
     ffmpeg -> build/fuse_demo.mp4 (video+AAC)
  5. `python3 tools/fuse_frames.py` - aligns Fuse frames to the headless replay (33/33 checkpoints pixel-identical last run),
     writes shots/fuse_v_*.png and shots/fuse_demo_run.gif
- Last Fuse run predates: dawn water-walk grace in rescue, longer Mare scene in bot -> redo steps 1-5.

## TODO
- [ ] test_game.py passing in ./build.sh
- [ ] re-run Fuse pipeline after the last code change
- [ ] design.md update (Mare roams, sabre L/R, as-built notes)
- [ ] retire maptool.py / data/rooms.asm / test_slice.py

## 2026-10-30 14:27 (Europe/London)
- Fixed enemy strike tests (1-frame input could fall in a no-tick frame; now 2 frames per input, wait 14 between swings; power-ups cleared).
- Added tools/progression.py: tile-level day/night flood fill with lantern/key/lever, all 160 rooms + 40 lights + 12 buds + 4 pieces reachable => COMPLETABLE. Pool lights need a <=3 tile bog wade (checked in-game: rooms 60/82/111 collectable).
- ./build.sh clean, 50/50 tests pass.
- NEXT: regenerate bot stream -> demo build -> replay_check -> Fuse recording -> wav/mp4/shots/gif.

## 2026-10-30 14:31 (Europe/London) - milestone: full game verified
- Bot route regenerated (1206 ticks), demo build replays headless (REPLAY OK, rooms 0,99,83,144,20,0,63,159,24,10,86,104; bridle 15; game_won).
- Fuse 1.6 + real 48.rom: build/fuse_demo.fmf -> fuse_demo.wav (143 s, 44.1k stereo, RMS ~1650) and fuse_demo.mp4 (h264+aac, 143 s); fuse_frames: 32/33 checkpoints pixel-identical (1 at dawn diff 0.98%), all named shots diff <=0.0004.
- shots/fuse_v_*.png (16) + shots/fuse_demo_run.gif (892 frames) regenerated and eyeballed.
- Retired slice files to attic/ (maptool.py, test_slice.py, data/rooms.asm, art/map.txt). ./build.sh clean, 50/50.
- Remaining (not built): night hags, boggart clods, faster wisps at night, 100% scroll; respawn tuning; packaging/art later.

## 2026-10-30 14:35 (Europe/London) - Phase 4 start: loose ends + balancing
Plan: (1) night hags (2) boggart clods (3) night wisps faster (4) 100% scroll (5) Mare visible on Mere
(6) normal-mode balance + no-god bot run (7) audio analysis + build/sfx clips; dawn-frame diff; re-record Fuse.
- 14:39 (5) Mare on the Mere DONE: gfx.py emits mare_occ (5x3 cell occupancy per frame/shift); on the Mere mare_draw snaps y to a cell, clears occupied cells to black + white ink, then draws her: white Mare on a cell-aligned shadow, no shared cells. Shot: shots/h_h_mare_shadow_a.png. (Enemies on the Mere still take lily colour - note.)
- 14:40 (3) night wisps DONE (1.0 -> 1.5 px/tick across, test added). 53/53.
- 14:41 (1) night hags DONE: type 9 (art hag_a/b, cyan), Mere rooms get night riser=hag (18 rooms, chosen by coords, map unchanged); AI blinks in at the far edge level with him, 3 px/tick, re-blinks at the other edge; gone at dawn; sfx_hag shriek. 4 tests added.
- 14:42 (2) boggart clods DONE: one clod (8x8 preshifted, yellow, own draw record) thrown when level & 36-150 px away (1/16 per tick), 4 px/tick, 40-tick life, stops at scenery; costs a life; sabre bats it away (+10). sfx_clod. 4 tests. 61/61.
- 14:44 (4) 100% saga scroll DONE: after the rating, go_pct==100 -> saga (lines rise row by row from the foot, any key ends). Shot shots/h_saga_scroll.png. 3 tests. 64/64. NEXT: (6) normal-mode balance + walking bot without god.

## 2026-10-30 15:15 (Europe/London) - box restart
- The box was reset around 15:00: the project came back from a ~14:56 snapshot without build/, and pasmo/Fuse were gone.
- Reinstalled from deb.debian.org with curl + dpkg (pasmo 0.5.3, fuse-emulator-sdl 1.6.0, fuse-emulator-utils, libspectrum8, sdl12-compat, libaudiofile1, opense-basic). ./build.sh: 62/62.
- Lost edits after the snapshot are being re-applied: walker look-ahead, heron wind-up, hit knock-back.

## 2026-10-30 15:27 (Europe/London) - resumed after 2nd interruption
- Tools still installed; re-applied edits present (heron wind-up 10 ticks + 3 px lunge, hit knock-back, boggart rests after a hit, walker look-ahead). ./build.sh 62/62.
- Backups: (development-box backup script, not included in the public repo).
- Walker status: reaches bit, lantern, rein; stalls at the north door of room 19 (narrow corridor, wisps hover below). Working on the fight logic.

## 2026-10-30 15:36 (Europe/London) - (7) audio listen-check
- New sound-check build: `./build.sh sfx` -> build/miremare_sfx.tap (engine/jukebox.asm plays all 16 effects one second apart; border shows the number).
- Recorded in real Fuse (`tools/fuse_demo.py 45 sfx`, fmfconv -> build/fuse_sfx.wav) and analysed with new `tools/audio_check.py sfx`:
  16/16 effects present, 0 clipped samples, no DC left after any effect, no pair too similar (spectral + duration check).
  Per-effect clips: build/sfx/01_swing.wav ... 16_tune.wav, plus build/sfx/all_effects.wav. Report: build/audio_report.json.
- Fixes from the check: hoof-beat (2 ms) and clod (3 ms) were mere clicks, hag shriek 6 ms; hit was spectrally identical to the menu blip.
  Now hoof = low 600 Hz thud + knock (7 ms), clod = whoosh + splat (15 ms), hag = falling shriek 4.4->2.3 kHz (23 ms), hit = falling "thock".
- Note: there is no footstep sound on dry ground (by design, as in Sabre Wulf); "step" = the squelch in bog.

## 2026-10-30 15:42 (Europe/London) - (6) balance: a real fairness bug found by the no-god walker
- The walker stalled at room 19's north door: a wisp rising straight up the doorway column could NOT be killed.
  Cause: sabre vertical reach (dy<14) was smaller than the body-hit band (dy<15), so a creature closing vertically always
  touched him before the blade could meet it. Fix: swing reach dy<20 (enemy.asm, eh_ext+20). Brute force from the saved
  stall state: 0/216 swing timings killed the wisp before, 123/216 survive (most with the kill) after.
- Tests 65/65: added "heron rears 8+ ticks then lunges <=3 px/tick", "struck boggart knocked back and rests",
  "a wisp rising straight at him can be cut down".
- Walker: safe-candidate scoring now = 2*score gain + progress to the next waypoint; leaving the room the wrong way
  costs -2000 (re-entry re-spawns the room); added double-swing candidates.

## 2026-10-30 15:58 (Europe/London) - (6) balance, continued
- tools/balance_runs.sh: no-god walker at look-ahead 12/8/6 ticks + reflex-only; logs build/walk_log_<tag>.json, summary build/_bal.log.
- First results (before the ox change): h12 won, 1-2 deaths; h8 won with 4 deaths; h6 lost (night death cascade); reflex-only lost by 2.8 min.
- Night cascade cause: deaths respawn him at the room entry with the killers still there. Now: after a death the screen's creatures
  return to their lairs (1 s + sparkle). Bog ox: 10 ticks pawing/bellow before a charge (it was instant: unavoidable in open rows).
- Tests 67/67 (+ ox warning, + creatures fall back after a death).
- Walker fixes: re-plan after the phase change re-generates the room; mixed day+night routes; when nothing is safe, delay the hit.
- God-mode bot (tools/bot.py) re-run on the current game: REPLAY OK; Fuse recording with sound in progress.

## 2026-10-30 16:20 (Europe/London) - final runs
- Demo stream is now packed (tools/pack_stream.py: 7-value table, 1 byte per run, part B moved to $5B00 at start-up) so a whole
  normal-mode game (16909 ticks, 2987 bytes) fits. replay_walk.py: the walker's recorded stream does NOT yet replay
  (diverges between frames 1611 and 7458, also in live mode) - walker stream recording bug, outstanding. God-mode stream REPLAY OK.
- ./build.sh: 69/69 tests pass.
- Final no-god walker runs (current build): h12 won, 3 deaths (monk r22 Abbey night, boggart r36 Wood night, heron r34 Wood night), 2 lives left, 12.1 min;
  h8 won, 2 deaths (boggart r1 Wood, ox r45 Peat Hags night), 3 left, 12.0 min; h6 lost (5 deaths, ox r45 x2 night, monks r41/42 night);
  reflex-only lost in 2.7 min (Sedge Fen herons/wisp).
- Dawn/"diff" frames: Fuse shows the headless screen of the adjacent frame or a split at a raster row (tearing while a
  sprite/dawn repaint is drawn as the beam passes). Game state stays in lockstep (every later checkpoint identical). Not a bug.
- 16:20 Fuse god-mode run re-recorded (155 s, sound): 31/33 checkpoints pixel-identical, other 2 = adjacent-frame/tearing; audio 0 clipped, 0 lone clicks.
