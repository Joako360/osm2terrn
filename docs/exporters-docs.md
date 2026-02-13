# Exporters — Deep Human Documentation (OSM2Terrn)

## Purpose & Audience
This document is the **authoritative human reference** for the exporter system that produces game-ready terrain assets. It explains formats, constraints, rationale, workflows, validation, and troubleshooting.

**Audience:** map authors, exporter developers, CI engineers, and PR reviewers.

**Goals:**
- Clarify responsibilities and boundaries of each file format.
- Provide reproducible authoring and QA workflows.
- Document common failure modes and concrete fixes.
- Enable automation (CI) to prevent regressions.

> This document is intentionally verbose for humans. Hard rules for machines live in `.github/instructions/`.

---

## Quick Summary (TL;DR)
- Units: **meters** everywhere.
- Coordinates: origin-centered local UTM.
- `.terrn2` = metadata + references (no objects).
- `.otc` = global terrain geometry, heightmap, paging, LOD.
- `*-page-X-Y.otc` = texture layers and blending per page.
- `.tobj` = all object instances, procedural roads, vegetation.
- Heightmaps: prefer **PNG (grayscale, (2^n)+1)**; RAW allowed but fragile.
- Validate early, fail fast; run validators locally and in CI.

---

## 1. Overall Architecture

Exporters generate **deterministic, game-ready terrain packages**. Each file type has a strict scope. Mixing responsibilities is the primary source of bugs.

| File | Responsibility |
|------|----------------|
| `.terrn2` | Terrain entry point, metadata, references |
| `.otc` | Global terrain geometry and rendering config |
| `*-page-X-Y.otc` | Texture layers and blend stacks |
| `.tobj` | Object instances, procedural roads, vegetation |

**Design principle:** separation of concerns. Metadata, geometry, textures, and objects must never be mixed across formats.

---

## 2. Coordinate System & Units

- **Units:** meters (no exceptions).
- **Coordinates:** local, origin-centered (0,0) projected in UTM.
- **Axes:** X/Z = horizontal plane; vertical axis in meters (per format convention).

### Numeric Precision
- Coordinates: 3 decimals.
- Widths/sizes: 2 decimals.

Rationale: higher precision adds noise without improving visual fidelity.

---

## 3. `.terrn2` — Terrain Entry Point

### Purpose
`.terrn2` is the **root configuration**. It defines identity and references, not content.

### Required Content
- `[General]` section with:
  - `Name`
  - `GeometryConfig`
  - `Gravity`
  - `CategoryID`
  - `Version`
  - `GUID`

### Optional Sections
`[Authors]`, `[Objects]`, `[Scripts]`, `[AssetPacks]`, `[AI Presets]`.

### Rules & Rationale
- MUST NOT contain object instances or procedural data.
- Keep minimal (< ~30 lines) to ease review and duplication.

---

## 4. `.otc` — Global Ogre Terrain Configuration

### Purpose
Defines terrain geometry, heightmap interpretation, paging, LOD, and rendering options.

### Heightmaps

#### PNG (Recommended)
- Grayscale image.
- Resolution auto-detected.
- Fewer failure modes.

Key:
```
Heightmap.0.0=mapname.png
```

#### RAW (Compatibility)
- Binary, usually 16-bit little-endian.
- Size and bpp **must** be declared and correct.
- Any mismatch can crash the engine.

Keys:
```
Heightmap.0.0.raw.size
Heightmap.0.0.raw.bpp
```

All heightmaps must use resolutions `(2^n) + 1` (e.g., 513, 1025, 2049).

### World Size

`WorldSizeX`, `WorldSizeZ`, `WorldSizeY` define real-world scale in meters and are **independent** of heightmap resolution.

---

## 5. `*-page-X-Y.otc` — Texture Layers & Blending

### Purpose
Defines base texture and blended detail layers for a single terrain page.

### Structure
1. Heightmap filename
2. Total layer count
3. (Optional) comment header
4. Base layer — **3 fields**
5. Blend layers — **6 fields each**

Base layer is the default surface. Blend layers are applied using blend maps and channels (`R`, `G`, `B`, `A`).

### Common Pitfalls
- Layer count mismatch.
- Using blend parameters in the base layer.
- Referencing missing DDS/PNG files.

---

## 6. `.tobj` — Objects, Roads, Vegetation

### Purpose
Defines everything placed on the terrain:
- Static objects
- Spawn zones and shops
- Procedural roads and rails
- Grass and trees

### Object Lines
```
x, y, z, yaw, pitch, roll, type file
```

- Coordinates in meters.
- Rotations in degrees.
- Order matters; objects are processed sequentially.

### Procedural Roads
- Prefer `begin_procedural_roads` / `end_procedural_roads` blocks.
- Better performance and maintainability than chained road objects.

### Global Headers
Optional directives such as `collision-tris`, `grass`, `trees`, `grid`, `set_default_rendering_distance` apply terrain-wide and typically appear at the top.

---

## 7. Authoring Workflow

1. Prepare DEM → resample to `(2^n)+1`.
2. Export heightmap (PNG preferred).
3. Create global `.otc`.
4. Create paged `*-page-X-Y.otc`.
5. Author `.tobj` (objects, roads, vegetation).
6. Create minimal `.terrn2`.
7. Run validators locally.
8. Commit and open PR with changelog.

---

## 8. Validation & QA

### Mandatory Checks
- `.terrn2`: required keys present.
- `.otc`: world sizes present; valid `PageSize`.
- `*-page-X-Y.otc`: correct layer count and field arity.
- `.tobj`: parsable object lines; valid headers.
- Heightmaps: PNG grayscale & size; RAW size/bpp/endianness.

### Tooling Examples
- PNG size: `identify -format "%w %h" map.png`
- RAW size sanity: `(width * height * bytes_per_pixel)`

---

## 9. Common Failure Modes

| Symptom | Cause | Fix |
|--------|-------|-----|
| Crash on load | RAW size mismatch | Re-export or switch to PNG |
| Flat/inverted terrain | Wrong flipX/flipY | Toggle flips or re-export |
| Missing textures | Wrong filename/path | Fix references |
| Blend not applied | Layer count/channel mismatch | Correct counts/channels |
| Performance drop | Low LOD or heavy grass | Tune `MaxPixelError`, density |

---

## 10. CI Integration

Automate validation in CI to block regressions.

Example GitHub Actions steps:
- Checkout repo
- Install ImageMagick + Python
- Run exporter validation script

Validators must fail with non-zero exit codes on errors.

---

## 11. Repository Layout & Naming

Recommended layout:
```
/terrain-name/
  /geometry/
  /pages/
  /objects/
  /assets/
  terrain.terrn2
  docs/
```

Use lowercase, hyphen-separated filenames. Keep GUIDs stable.

---

## 12. Review Checklist

- Heightmap resolution verified.
- Required `.terrn2` keys present.
- No unexpected object reordering.
- All referenced assets exist.
- Performance-sensitive changes documented.

---

## 13. Principles (Summary)

- Separation of concerns
- Deterministic output
- Explicit validation
- Documentation for humans, rules for machines

---

## Appendix — Minimal Examples

### Minimal `.terrn2`
```
[General]
Name=ExampleTerrain
GeometryConfig=example.otc
Gravity=-9.81
CategoryID=129
Version=2
GUID=10282f4b-038b-4700-827b-e39d5ea0f5c7
```

### Minimal `.otc`
```
Heightmap.0.0=mapname.png
WorldSizeX=3000
WorldSizeZ=3000
WorldSizeY=300
PageSize=1025
```
