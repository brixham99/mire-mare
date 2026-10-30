# Mire Mare packaging (Phase 5) - notes
Started 2026-10-30 16:45 (Europe/London).

## Refs studied
Sabre Wulf / Knight Lore / Underwurlde / Nightshade / Alien 8 inlays, box scans and tape labels in ../../refs.
- Big-box insert = one long fold-out card: outer side [credits strip | spine title | front (48K line, logo, art, badge) | CONTROLLING YOUR EXPLORER | LOADING INSTRUCTIONS + GUARANTEE + COPYRIGHT]; inner side [prose + riddle | prose | FEATURES 2-col + footer + cat. no.]. White bold Times-style serif on black, centred CAPS headings.
- Box fronts: matte black, "48K SINCLAIR ZX SPECTRUM" in bold serif top, hand-lettered logo, art in a ruled frame (Nightshade/Alien 8), ULTIMATE badge bottom centre. No screenshots, no credits.
- Tapes: solid-colour label (red, orange, maroon), white print: title logo L+R, ruled ULTIMATE box, diagonal stripes in the corners, small copyright line.

## Decisions
- Painting: 4 GenerateImage attempts (src/cover_a..d.jpg). Chose **C** (vignetted on black, vivid gouache/airbrush, Sabreman on a tussock facing the rearing Night Mare under a moon) - closest to Ultimate's Nightshade/Alien 8 look and it reads at loading-screen size. A = good but more "storybook", B = realistic, D = close-up portrait, too modern.
- Painting source is 768x1024; upscaled ~1.8x with Lanczos + unsharp + painted-board grain for 300 dpi. Fine at box size; a higher-res repaint would be needed for a real print run of the poster.
- Lettering composed in Pillow (src/lib.py): Metal Mania base glyphs, warped for a hand-lettered wobble, mire drips, moon-white->violet airbrush fill, white keyline, black outline. Badge: own chrome-band ULTIMATE / PLAY THE GAME in a ruled black box (Russo One base), drawn not copied.
- Sizes (300 dpi, all with 3 mm bleed): box front 135x195 mm; spines 25 mm deep (estimate - real box measured ~19x13.5 cm face); inlay 412x180 mm; cassette label 102x64 mm.
- Catalogue number 481013 is invented in the 4810xx series of the Sabre Wulf inlay.
- Tape label: cassette labels have 2 mm bleed. Side A and B differ only in the side letter; the spindle window is transparent (RGBA).

## Loading screen (src/mkscr_cover.py -> art/loading_final.scr -> data/loading.scr)
- The layout follows the Knight Lore SCREEN$: picture left, title cloud right, badge bottom right, and a thick 2-cell decorative border (bevelled cyan rules, chevron stitching, red/yellow corner roundels).
- Picture: painting C cropped, boosted and converted to 120x160 px on black paper. Each 8x8 cell gets ONE ink chosen by hue. Pale areas use white ink, the burning eyes red ink, and the rest the nearest of B/R/M/G/C/Y, with BRIGHT on light cells. Luminance becomes 8x8 Bayer ordered dither, which gives an engraved look. The game's own Sabreman sprite is overlaid so he reads at this size.
- Title is pixel-lettered from Metal Mania 40 px with a hollow white keyline and drips, on a cell-aligned magenta/blue cloud. The badge is a white-ruled box with green ULTIMATE and cyan PLAY THE GAME.
- The legality check confirms max 2 colours per 8x8 cell. The file is 6912 bytes.
- Install: tools/mkscr.py now copies art/loading_final.scr to data/loading.scr if it exists. The old placeholder generator is kept as tools/mkscr_placeholder.py and still runs as a fallback. ./build.sh passes 69/69 tests, and data/loading.scr is byte-identical to art/loading_final.scr.
- Fuse verification (src/fuse_loadtest.py): fuse-sdl 48K with ../roms/48.rom, --no-traps --no-fastload --no-accelerate-loader (real-speed edge loading). It types LOAD "" and presses ENTER. The tape blocks take ~206 s in total. Screenshots are in out/06_fuse_load_*.png. Note that --auto-load did nothing with this setup, so the keys are typed instead.
- This is an automated conversion. A hand-pixelled pass over the horse's head and mane would improve it, which is how Ultimate's artists actually worked.

## Extras
- 05_advert_A4: full-page advert, 210x297 mm + bleed. Logo, framed painting, badge, "48K SINCLAIR ZX SPECTRUM  £9.95" and a small order line. No screenshots, as in Ultimate's ads.
- 05_poster_A3: painting full-bleed with logo and badge. The painting is upscaled ~4.5x, so it will look soft at A3. It needs a hi-res repaint before any real print.
- 07_mockup.png: a 2D composite (perspective quads, drop shadows, drawn cassette shell, vignette), 3600x2400.
- PDFs: one per piece at real size (Pillow, 300 dpi, JPEG-compressed images) plus MIRE_MARE_packaging_all.pdf (10 pages).
