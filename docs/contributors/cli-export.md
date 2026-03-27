# CLI: export flow (`export`)

`export()` performs processing and file generation:

1. Validates that `current_map.data` exists.
2. Generates:
   - `<place>_heightmap.png`
   - `<place>_groundmap.png`
3. Attempts procedural roads generation.
4. Computes world params from bounds.
5. Exports:
   - `<place>-page-0-0.otc`
   - `<place>.otc`
   - `<place>.terrn2`
6. Ensures fallback `<place>.tobj` exists.

Road export is optional and skipped on pipeline errors.
