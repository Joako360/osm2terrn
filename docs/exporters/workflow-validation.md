# Export workflow and validation

## Recommended workflow

1. Prepare DEM and resample to `(2^n)+1`.
2. Export heightmap (prefer PNG).
3. Generate global `.otc`.
4. Generate paged `*-page-X-Y.otc`.
5. Generate `.tobj`.
6. Generate minimal `.terrn2`.
7. Validate locally before PR.

## Mandatory checks

- `.terrn2`: required keys exist.
- `.otc`: world sizes + page size are valid.
- Paged `.otc`: layer count and field arity are correct.
- `.tobj`: object lines and headers are parseable.
- Heightmap format matches configuration.

## Useful local checks

- PNG size: `identify -format "%w %h" map.png`
- RAW size sanity: `width * height * bytes_per_pixel`
