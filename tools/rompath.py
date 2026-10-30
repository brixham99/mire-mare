"""rompath.py - where to find a 48K Spectrum ROM image (NOT included in this repo).
Set MIREMARE_ROM=/path/to/48.rom, or drop the file at roms/48.rom (gitignored)."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM48 = os.environ.get('MIREMARE_ROM') or os.path.join(ROOT, 'roms', '48.rom')
if not os.path.isfile(ROM48):
    raise SystemExit('Mire Mare tools need a 48K ROM image: set MIREMARE_ROM or put it at roms/48.rom')
