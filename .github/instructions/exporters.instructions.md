---
applyTo: "src/processing/*.py"
---

# Exporters — Copilot-Optimized Instructions

## Objective
Provide short, executable rules so GitHub Copilot generates **correct, deterministic exporters**. This file contains **only hard rules, validations, and minimal examples**. All extended explanations belong in `docs/`.

---

## ABSOLUTE RULES (HIGHEST PRIORITY — ALWAYS APPLY)
1. **Units**: meters (m) for all values.
2. **Order**: preserve input order exactly; **do NOT reorder** objects or lines.
3. **`.terrn2` scope**: MUST NOT contain object instances, procedural roads, or placements.
4. **Float formatting**:
   - Widths: `"{:.2f}"`
   - Coordinates: `"{:.3f}"`
5. **Files**: always end with a final newline.
6. **Fatal errors** (must be detected and reported):
   - RAW heightmap size mismatch.
   - Missing required keys in `.terrn2` (`Name`, `GeometryConfig`, `Gravity`, `CategoryID`, `Version`, `GUID`).

If rules conflict, apply them in the order listed above.

---

## Core Conventions (MEDIUM PRIORITY)
- **Coordinates**: local, origin-centered (0,0) projected in UTM; Z in meters.
- **Comments**: `#`, `;`, or `//` only.
- **Formats**:
  - `.terrn2` / `.otc`: INI-style.
  - `*-page-X-Y.otc`: first line is the heightmap filename.
- **Heightmaps**:
  - PNG preferred for new terrains (grayscale, auto-detected size).
  - RAW allowed for compatibility; requires `raw.size` and `raw.bpp`.

---

## Mandatory Validations (Copilot must perform or emit checks)

### `.terrn2`
- `[General]` section present.
- Required keys present: `Name`, `GeometryConfig`, `Gravity`, `CategoryID`, `Version`, `GUID`.
- No object instances or roads inside this file.

### Global `.otc`
- `WorldSizeX`, `WorldSizeZ`, `WorldSizeY` present (meters).
- `PageSize` equals `(2^n) + 1`.
- `PagesX` / `PagesZ` sane (0 for single page).
- RAW heightmap: `Heightmap.0.0.raw.size` matches actual file size.

### `*-page-X-Y.otc`
- Line 1 references the correct heightmap (RAW or PNG).
- Line 2 layer count matches the number of layer lines.
- Base layer: exactly **3 fields**.
- Blend layers: exactly **6 fields**.

### `.tobj`
- Object line format:
  `x, y, z, yaw, pitch, roll, type file`
- `collision-tris` (if present) is an integer.

### Heightmap Files
- PNG: grayscale, resolution `(2^n) + 1`.
- RAW: correct `raw.size`, `raw.bpp`, little-endian for 16‑bit.

---

## Minimal Examples (ONE per format only)

### Minimal `.terrn2`
```
[General]
Name=ExampleTerrain
GeometryConfig=example.otc
Gravity=-9.81
CategoryID=129
Version=2
GUID=00000000-0000-0000-0000-000000000000
```

### Minimal global `.otc`
```
Heightmap.0.0=mapname.png
WorldSizeX=3000
WorldSizeZ=3000
WorldSizeY=300
PageSize=1025
```

### Minimal `*-page-0-0.otc`
```
mapname.png
2
3000, base.dds, base_NRM.dds
6, detail.dds, detail_NRM.dds, blend.png, R, 1
```

### Minimal `.tobj`
```
2531.863, 5.971, 410.735, 0.000, 0.000, 0.000, truck wrecker.truck
```

---

## Expected Copilot Behavior
- Generate **only required fields first**; mark optional fields with comments.
- Validate before proposing output; **report fatal errors explicitly**.
- Do not add long explanations, history, or extra examples.
- If an example conflicts with an ABSOLUTE RULE, **fix the example**.

---

## Maintenance Rule
Keep this file **≤ 700 words**. All detailed documentation, comparisons, and tutorials must live in `docs/` and not here.

