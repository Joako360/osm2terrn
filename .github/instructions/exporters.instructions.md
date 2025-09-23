---
applyTo: "src/processing/*.py"
---

# Exporters – Instructions (OSM2terrn)
Repository-wide conventions for generating game-ready files.

Location: `.github/instructions/exporters.instructions.md`

---

## 0) General conventions
- **Units**: meters (m).
- **Coordinates**: local, origin-centered (0,0) at `origin_lon, origin_lat` projected in UTM; Z in meters.
- **Float formatting**:
  - Widths: `"{:.2f}"`
  - Coordinates: `"{:.3f}"`
- **Ordering**: Preserve input order; exporters must not reorder.
- **Newline**: Always end files with a final newline.

---

## 1) `.terrn2` – Terrain Entry Point
### Purpose
Main terrain configuration file for Terrn2. Contains only basic metadata, references to geometry, object, and texture files, and global settings. Does NOT contain procedural roads or object instances directly.

### Structure and Typical Fields
- **INI-style sections**: `[General]`, `[Authors]`, `[AssetPacks]`, `[Objects]`, `[Scripts]`, `[AI Presets]`, etc.
- **[General]**: Terrain name, geometry config, water settings, ambient color, start position, gravity, category, version, GUID, and optional fields like sky/weather config, traction map, sandstorm cubemap, etc.
- **[Authors]**: List of contributors for terrain, objects, updates, etc.
- **[Objects]**: References to one or more `.tobj` files (object catalogs and placements).
- **[Scripts]**: Optional, references to race or logic scripts.
- **[AssetPacks]**: Optional, references to asset packs for extra objects/vegetation.
- **[AI Presets]**: Optional, references to AI waypoint files.

### Recommendations
- Use clear and descriptive names for all referenced files.
- Maintain the INI structure and avoid adding data blocks (like procedural roads or object instances) directly in `.terrn2`.
- Multiple `.tobj` files can be listed in `[Objects]` for modularity (e.g., separating vegetation, props, roads).
- Comments (`#` or `//`) are allowed and often used for documentation or disabling fields.
- All values should be in meters and local coordinates unless specified otherwise.

### Example (based on real maps)
```
[General]
Name = North St Helens
GeometryConfig = a1da0UID-nhelens.otc
Water = 1
WaterLine = 33
AmbientColor = 0.93, 0.86, 0.76
CaelumConfigFile = nhelens-sky2.os
StartPosition = 1162.73 34.9059 941.82
TractionMap = a1da0UID-nhelens-landuse.cfg
Gravity = -9.81
CategoryID = 129
Version = 2
GUID = 8454a8dc-bfa3-4cb4-8aa0-662601ddba05
SandStormCubeMap = tracks/skyboxcol

[Authors]
terrain = pricorde
objects = various
update = klink
update2 = CuriousMike

[Objects]
a1da0UID-nhelens.tobj=
vegetation.tobj=

[Scripts]
a1da0UID-nhelens.as=
race_logic.as=

[AssetPacks]
industrial-objects.assetpack=
fancy-trees.assetpack=

[AI Presets]
nhelens_waypoints.json=
```

### Notes from Example Analysis
- The `[General]` section is always present and contains all global settings.
- The `[Objects]` section can list several `.tobj` files for different object types.
- The `[Authors]` section may include multiple contributors and update credits.
- Optional sections like `[AssetPacks]` and `[AI Presets]` are used for advanced terrains.
- Scripts and logic files are referenced in `[Scripts]`.

---

## 2) `.otc` – Ogre Terrain Config (global)
### Purpose
Defines the terrain geometry, heightmap, world size, page size, and rendering options for Terrn2. The global `.otc` file is referenced by `.terrn2` and contains keys for terrain pages, heightmap files, world size, and rendering options. Does NOT contain object placements.

### Structure and Typical Fields
- **INI-style key-value pairs**: Each line defines a property of the terrain or rendering system.
- **Heightmap settings**: `Heightmap.0.0.raw.size`, `Heightmap.0.0.raw.bpp`, `Heightmap.0.0.flipX`.
- **World size**: `WorldSizeX`, `WorldSizeZ`, `WorldSizeY` (meters).
- **Page size and format**: `PageSize`, `PageFileFormat` (pattern for paged .otc files).
- **Rendering options**: `disableCaching`, `MaxPixelError`, `LightmapEnabled`, `SpecularMappingEnabled`, `NormalMappingEnabled`, `LayerBlendMapSize`, `minBatchSize`, `maxBatchSize`.
- **Other**: Comments (`#` or `;`) are allowed for documentation.

### Recommendations
- Use clear and descriptive values for all keys.
- Maintain the INI structure and avoid adding object instances or unrelated data.
- The `PageFileFormat` should match the naming pattern of paged .otc files.
- All sizes and coordinates should be in meters.

### Example (based on real maps)
```
Heightmap.0.0.raw.size=1025
Heightmap.0.0.raw.bpp=2
Heightmap.0.0.flipX=0

WorldSizeX=3000
WorldSizeZ=3000
WorldSizeY=281
PageSize=1025

disableCaching=1

PageFileFormat=a1da0UID-nhelens-page-0-0.otc

MaxPixelError=1
LightmapEnabled=1
SpecularMappingEnabled=1
NormalMappingEnabled=1
LayerBlendMapSize=2048
minBatchSize=17
maxBatchSize=65
```

### Notes from Example Analysis
- The `.otc` global file configures the terrain's geometry, heightmap, and rendering, not object placements.
- The `PageFileFormat` links to paged .otc files for ground textures and blending.
- Comments and extra keys may be present for optimization and documentation.

---

## 3) `*-page-X-Y.otc` – Paged Ogre Terrain Config
### Purpose
Defines the ground textures and blending for a specific terrain page/tile. Each paged `.otc` file configures the textures and blending for its tile, referenced by the main `.otc` file. Does NOT contain object placements.

### Structure and Typical Fields
- **First line**: Heightmap or texture file name for the tile.
- **Second line**: Number of layers.
- **Third line**: Header describing the columns (worldSize, diffusespecular, normalheight, blendmap, blendmapmode, alpha).
- **Subsequent lines**: Parameters for each layer, separated by commas.
  - Example: `6, terrain_detail.dds, blank_NRM.dds, tile_rgb.png, R, 0.5`

### Recommendations
- Keep the order and format of fields as observed in real examples.
- Use descriptive names for texture and blending files.
- The values for worldSize and alpha should be consistent with the global config.

### Example (based on real maps)
```
example.png
2
; worldSize, diffusespecular, normalheight, blendmap, blendmapmode, alpha
6, terrain_detail.dds, blank_NRM.dds, example_rgb.png, R, 0.5
6, terrain_grass.dds, blank_NRM.dds, example_rgb.png, G, 0.5
```

### Notes from Example Analysis
- The paged `.otc` file defines textures and blending for each tile/page.
- The number of layers and parameters may vary depending on the terrain.
- Does not contain object instances or global geometry data.

---


## 4) `.tobj` – Terrain Object Definition, Procedural Roads & Rail Tracks
### Purpose
Defines object instances for the terrain, specifying position, rotation, type, and reference file. May include optional headers (e.g., collision-tris) and comments. For railways, also includes rail track segments and train spawners. Does NOT contain mesh/material definitions.

### Structure and Typical Fields
- **Optional header**: `collision-tris <int>` for collision info.
- **Object instances**: Each line: `<x>, <y>, <z>, <yaw>, <pitch>, <roll>, <type> <file>`
- **Rail track segments**: Use type `rail` or custom type, referencing mesh/odef/material files.
- **Train spawners**: Use type `trainspawner` or similar, referencing spawner mesh/odef.
- **Comments**: Use `//` for documentation or to disable lines.
- **Object types**: truck, load, machine, road-block, boat, dock, sign, trafficlight, rail, trainspawner, etc.
- **Referenced files**: `.truck`, `.load`, `.boat`, `.fixed`, `.sign`, `.mesh`, `.odef`, etc.

### Recommendations
- Keep the field format and structure as observed in real examples.
- Use comments for documentation and disabling lines.
- The `collision-tris` header is optional and specific for collisions.
- For rail tracks, use mesh and odef files with correct gauge and collision geometry.
- Train spawners should be placed at correct coordinates and flagged for RoR compatibility.
- Do not include mesh/material definition blocks or procedural roads, except for legacy compatibility.

### Example (based on real maps)
```
collision-tris 750000

1170, 33.7, 1022.7, 0.000000, -90, 0, truck monorail.truck
1191.162109, 35.034180, 930.908203, 0.000000, 0.000000, 0.000000, truck wrecker.truck
1131.103516, 35.034180, 910.888672, 0.000000, 0.000000, 0.000000, load acontainer.load
850.757690, 36.987686, 1580.171631, 0.000000, 38.000000, 180.000000, road-block1
414.818420, 38.000000, 941.014038, 0.000000, 112.500000, 0.000000, largedockoutercorner
// Rail track segment
952.270203, 9.000000, 2756.340332, -0.000000, -180.000000, -0.000000, rail rail1t100mstrt.mesh
// Train spawner
952.270203, 9.000000, 2756.340332, -0.000000, -180.000000, -0.000000, trainspawner RCa474UID_trainspawner.mesh
// Example comment
```

### Notes from Example Analysis
- The `.tobj` file contains object instances with position, rotation, and type, referencing definition files.
- Rail tracks and train spawners use mesh/odef/material files and must be placed with correct coordinates and orientation.
- Comments are common and useful for documentation.
- The `collision-tris` header appears in maps with complex collisions.
- No mesh/material definition blocks or procedural roads are observed in modern Terrn2 examples.
- Some `.tobj` files may include global parameters or configuration lines (e.g., grass settings, density, material) at the top of the file. This demonstrates the format's flexibility to include special terrain-wide settings alongside object instances.

---

## 5) Heightmaps (raw/PNG)
### Purpose
Provide terrain elevation. Used to shape the terrain surface. Roads and objects are placed relative to Z=0 until DEM sampling.

### Structure and Typical Fields
- Heightmaps are typically stored as 16-bit RAW files (`.raw`) or PNG images (`.png`).
- The heightmap file must match the resolution and format specified in the `.otc` config (e.g., `Heightmap.0.0.raw.size`, `Heightmap.0.0.raw.bpp`).
- The origin and scale (meters per pixel) must be consistent with the terrain's world size.
- PNG heightmaps should be grayscale, with pixel values mapped to elevation.
- RAW heightmaps are usually little-endian (`raw16le`), with each pixel representing elevation in meters.

### Recommendations
- Always provide a sidecar JSON with metadata (format, size, meters per pixel, origin).
- Use lossless formats (PNG or RAW) to avoid artifacts in terrain generation.
- Ensure the heightmap covers the entire terrain area defined in the `.otc` file.
- For best results, preprocess heightmaps to remove spikes, holes, or unrealistic features.
- When using PNG, avoid color channels—use single-channel grayscale only.

### Example sidecar JSON (based on real maps)
```json
{
  "type": "heightmap",
  "format": "raw16le",
  "size": {"width": 2048, "height": 2048},
  "meters_per_pixel": 1.0,
  "origin_lm": {"x": 0.0, "y": 0.0}
}
```
Or for PNG:
```json
{
  "type": "heightmap",
  "format": "png",
  "size": {"width": 1024, "height": 1024},
  "meters_per_pixel": 2.0,
  "origin_lm": {"x": 0.0, "y": 0.0}
}
```

### Notes from Example Analysis
- Heightmaps are referenced in the `.otc` file and must match the expected resolution.
- The elevation range should be normalized to the terrain's vertical scale (`WorldSizeY`).
- Artifacts in the heightmap can cause terrain glitches; always validate before export.

---

## 6) Intermediate JSON (debug)
### Purpose
Developer-only artifact mirroring the Road dataclass or other internal structures. Used for debugging and inspection before export.

### Example
```json
{
  "roads": [
    {
      "width": 7.0,
      "border_width": 0.0,
      "border_height": 0.0,
      "type": "residential",
      "points_m": [[-12.345, 56.789, 0.0], [0.0, 10.0, 0.0]]
    }
  ]
}
```

---

## 7) Validation
- `.terrn2`: Must have valid INI sections and references, no procedural roads blocks.
- `.otc` and `*-page-X-Y.otc`: Header present, correct columns per line.
- `.tobj`: Must have `name`, `mesh`, `material`. Procedural roads block is optional.
- All files must end with a newline.

