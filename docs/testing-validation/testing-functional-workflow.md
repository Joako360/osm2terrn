# Testing: functional workflow

This is a proposal for a future bounded validation, not an instruction to run
network or terrain operations in every change. The manual bbox route currently
returns before download because the selected area has no place label; use only
a supported selection path until that behavior is changed and tested.

1. Start the declared package entry in a disposable environment (installation and interactive execution are not verified here).
2. If a bounded external request is separately authorized, select an area via the currently supported place-search route and constrain outputs.
3. Export only within that explicitly scoped validation.
4. Validate artifact presence in `output/`:
   - `<place>_heightmap.png`
   - `<place>_groundmap.png`
   - `<place>.otc`
   - `<place>-page-0-0.otc`
   - `<place>.terrn2`
   - `<place>.tobj`
