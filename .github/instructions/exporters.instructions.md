---
applyTo: "osm2terrn/processing/*.py"
---

# Exporter Rules

## Scope

Terrn2Exporter -> .terrn2
OTCExporter -> .otc
TOBJExporter -> .tobj
HeightmapExporter -> PNG / RAW

Do not generate files outside exporter scope.

## Critical Rules

- Units: meters.
- Preserve input order exactly.
- Output must be deterministic.
- Always end files with a newline.
- Do not use scientific notation.

Formatting:
- Widths -> {:.2f}
- Coordinates -> {:.3f}

Terrn2:
- Must not contain object instances.
- Must not contain procedural roads.

## Validations

Terrn2:
- [General] required.
- Required keys:
  - Name
  - GeometryConfig
  - Gravity
  - CategoryID
  - Version
  - GUID

Global OTC:
- WorldSizeX present.
- WorldSizeY present.
- WorldSizeZ present.
- PageSize = (2^n)+1.

Page OTC:
- Line 1 = heightmap filename.
- Line 2 = layer count.
- Base layers = 3 fields.
- Blend layers = 6 fields.

TOBJ:
- Object format:
  x,y,z,yaw,pitch,roll,type,file
- collision-tris integer.

Heightmaps:
- PNG grayscale.
- Resolution = (2^n)+1.
- RAW size validation required.
- RAW little-endian 16-bit.

## Fatal Errors

- RAW size mismatch.
- Missing mandatory terrn2 keys.

## Output Rules

- Validate before exporting.
- Report fatal errors explicitly.
- Generate only required fields.
- Do not generate placeholders.
- Do not generate explanatory text.