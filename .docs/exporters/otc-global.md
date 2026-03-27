# Global `.otc` reference

## Purpose

Defines global terrain geometry, heightmap interpretation, paging and LOD.

## Heightmap formats

### PNG (recommended)
- Grayscale.
- Resolution auto-detected.
- Lower risk of format mismatch.

Key example:
```ini
Heightmap.0.0=mapname.png
```

### RAW (compatibility)
- Usually 16-bit little-endian.
- Requires explicit size and bpp.
- Mismatches can crash or corrupt terrain.

Key examples:
```ini
Heightmap.0.0.raw.size
Heightmap.0.0.raw.bpp
```

## Resolution rule

Heightmap resolution should be `(2^n)+1` (e.g. 513, 1025, 2049).

## World size keys

- `WorldSizeX`
- `WorldSizeZ`
- `WorldSizeY`

These define real-world scale in meters and are independent from raster resolution.
