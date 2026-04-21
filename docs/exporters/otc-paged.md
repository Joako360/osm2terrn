# Paged `*-page-X-Y.otc` reference

## Purpose

Defines texture layers and blending for each terrain page.

## Structure

1. Heightmap filename
2. Layer count
3. Optional comments/header
4. Base layer (3 fields)
5. Blend layers (6 fields each)

## Notes

- Base layer is the default surface.
- Blend layers use blend maps and channels (`R`, `G`, `B`, `A`).

## Common mistakes

- Layer count mismatch.
- Using blend fields in base layer definition.
- Referencing missing texture files.
