# `.tobj` reference

## Purpose

Contains terrain object placement and procedural content:

- Static objects
- Spawn zones / shops
- Procedural roads and rails
- Grass and trees

## Object line format

```text
x, y, z, yaw, pitch, roll, type file
```

- Coordinates in meters.
- Rotations in degrees.
- Lines are processed sequentially.

## Procedural roads

Procedural roads define road networks using waypoints with position, rotation, and styling parameters.

### Syntax

```text
begin_procedural_roads
 posX, posY, posZ,   rotX, rotY, rotZ,   width,   borderWidth, borderHeight, type
 ...more waypoints...
end_procedural_roads
```

All fields are required. **Commas are mandatory everywhere** — parsing fails if commas are missing.

### Parameters

| Parameter | Unit | Description |
|-----------|------|-------------|
| `posX, posY, posZ` | meters | Position in a local RoR coordinate system. X and Z are horizontal local meters, Y is elevation. |
| `rotX` | degrees | Pitch/roll for slope. Positive = elevation gain. Affects mesh geometry. |
| `rotY` | degrees | Yaw (compass direction). 0°=+X, 90°=-Z, 180°=−X, −90°=+Z. Anticlockwise around up axis. |
| `rotZ` | degrees | Roll (minimal visible effect; may skew textures). |
| `width` | meters | Road surface width. Respected by `flat`, `both` types only. |
| `borderWidth` | meters | Shoulder/border width. |
| `borderHeight` | meters | Border elevation relative to road surface. |
| `type` | enum | Road style: `flat`, `left`, `right`, `both`, `bridge`, `bridge_no_pillars`, `monorail`, `monorail2`. Unknown types fallback to defaults. |

### Example

```text
begin_procedural_roads
  10.000, 1.000, 10.000,    0, 0, 0,     2.00, 1.00, 1.00,    both
  20.000, 1.000, 10.000,    0, 0, 0,     3.00, 1.00, 1.00,    both
  30.000, 1.000, 10.000,    0, 0, 0,     4.00, 1.00, 1.00,    both
end_procedural_roads
```

### CRS-based export flow

The exporter now projects source geometry into a local RoR metric CRS before generating procedural road points.

- The map origin is defined by `origin_lon` / `origin_lat`.
- Source geometries are transformed from WGS84 or the source graph CRS into a custom local CRS centered on that origin.
- This local CRS is an Azimuthal Equidistant projection, so meter distances are preserved locally around the map center.
- After projection, the exporter outputs RoR local meters where X grows east and Z grows south.

Example origin setup from the CLI/download flow:

```python
origin_lon = (bbox_obj.west + bbox_obj.east) / 2.0
origin_lat = (bbox_obj.south + bbox_obj.north) / 2.0
```

Or from the environment variables used by the export pipeline:

```text
OSM2TERRN_ORIGIN_LON=-58.5208
OSM2TERRN_ORIGIN_LAT=-34.7556
```

This removes the previous UTM/local-space offset pipeline and keeps road coordinates aligned with the RoR world origin conventions.

### Critical Implementation Notes

1. **Type parameter quirk**: Only `flat` and `both` fully respect `width`, `borderWidth`, `borderHeight`. Other types (e.g., `road`) revert to hardcoded defaults.
2. **Border texturing**: Large border values show visible scaling/stretching artifacts. Keep values modest (0.5–2.0 for typical roads).
3. **Rotation handling**:
   - `rotX` (pitch) controls elevation slope; use positive values for uphill sections.
   - `rotY` (yaw) controls direction. Test with cardinal directions (0°, ±90°, 180°).
   - `rotZ` (roll) has minimal effect on mesh; mainly affects texture orientation.
4. **Coordinate precision**: Use floats (e.g., `10.000` not `10`). Missing decimals may cause parsing errors.
5. **Multi-segment continuity**: Each waypoint in a `begin_procedural_roads` block connects sequentially; ensure smooth transitions between rotations and positions.

### Best Practices

- **Test cardinal directions first**: 0° (+X), −90° (+Z), 180° (−X), 90° (−Z) are most predictable.
- **Avoid sharp rotations**: Large yaw changes between consecutive waypoints create unrealistic road geometry.
- **Use multiple blocks** for complex networks: One `begin_procedural_roads` block per logical road segment for clarity.
- **Validate dimensions**: Roads wider than ~15m may behave unexpectedly; borders should be 0.5–2.0m typically.
- **Grid alignment**: In multi-page terrains, use `grid` directives to ensure roads span page boundaries correctly.

## Coordinate system (top-down view)

The supplied diagram (`.examples/roadbox-terrn/RoR CRS.drawio.svg`) shows the axis and angle convention used by `.tobj` files and by the exporters.

- Axes (top-down, Y up):
  - `+X` = East
  - `-X` = West
  - `+Z` = South
  - `-Z` = North

- Angle convention for `rotY` (yaw):
  - `0°` points to `+X` (East)
  - `90°` points to `-Z` (North)
  - `180°` points to `-X` (West)
  - `-90°` (or `270°`) points to `+Z` (South)

Notes:
- The `roadbox.tobj` example and the diagram use `-Z` as North; this convention is implemented in `osm2terrn/processing/road_geometry.py` (yaw computed with `atan2(dz, dx)`) and in the exporters.
- When generating `rotY` from a compass/geodetic bearing, normalize the source bearing to the RoR convention: compute the geographic bearing and convert it to RoR yaw before exporting.

## Optional global directives

Common top-level headers include `collision-tris`, `grass`, `trees`, `grid`, and `set_default_rendering_distance`.
