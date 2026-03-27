# Testing: functional workflow

When behavior changes, run an end-to-end smoke check:

1. Start CLI: `python main.py`
2. Download with a small bbox.
3. Export terrain.
4. Validate artifact presence in `output/`:
   - `<place>_heightmap.png`
   - `<place>_groundmap.png`
   - `<place>.otc`
   - `<place>-page-0-0.otc`
   - `<place>.terrn2`
   - `<place>.tobj`
