# Troubleshooting: terrain config issues

## Broken/missing `.otc`
- Validate bounds before world-parameter computation.
- Verify heightmap/groundmap filenames passed to exporter.

## `.terrn2` references missing files
- Check object file existence before appending to list.
- Keep placeholder `.tobj` as fallback when needed.
