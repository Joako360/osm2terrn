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

Prefer `begin_procedural_roads` / `end_procedural_roads` blocks when possible.

## Optional global directives

Common top-level headers include `collision-tris`, `grass`, `trees`, `grid`, and `set_default_rendering_distance`.
