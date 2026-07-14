---
applyTo: "osm2terrn/**/*.py"
---
# Heightmap Rules

## Purpose

Heightmaps represent terrain elevation surfaces used for terrain generation.

A heightmap is a terrain representation, not a generic image.

The primary goal is to generate coherent, realistic, and usable terrain.

---

## Elevation

* Elevation values represent terrain height.
* Elevations use meters.
* Preserve relative elevation relationships whenever possible.
* Preserve major terrain features during processing.

---

## Spatial Consistency

Heightmaps should remain spatially aligned with:

* terrain models
* road networks
* railways
* buildings
* other generated features

Avoid unintended spatial offsets between datasets.

---

## Terrain Continuity

Terrain processing should produce coherent and realistic terrain surfaces.

Preserve:

* terrain continuity
* major terrain features
* relative elevation relationships

Favor terrain realism and usability over strict preservation of incomplete source data.

Avoid processing that significantly distorts terrain structure.

---

## Terrain Processing

Interpolation, smoothing, filtering, and blending are valid terrain processing operations.

Processing should:

* improve terrain quality
* improve terrain usability
* preserve terrain characteristics
* minimize artifacts

Avoid destructive processing that removes important terrain features.

---

## Missing Data

Missing elevation data may be reconstructed using appropriate terrain processing techniques.

Allowed approaches include:

* interpolation
* smoothing
* filtering
* blending

Reconstructed terrain should remain consistent with surrounding terrain characteristics.

Avoid arbitrary elevation values that are not supported by nearby terrain.

---

## Resolution

Resolution should balance:

- terrain detail
- terrain quality
- processing cost
- memory usage
- simulator compatibility

Resampling is allowed when required for:

- terrain generation
- terrain processing
- dataset integration
- performance optimization
- output compatibility

Preserve overall terrain characteristics during resampling whenever practical.

---

## Validation

Validate:

* dimensions
* elevation ranges
* missing values
* spatial consistency

Invalid terrain data should fail early.

---

## Generation Rules

Preserve source elevation information whenever practical.

Keep heightmap generation deterministic and reproducible.

Reuse existing terrain processing utilities whenever possible.

Avoid duplicate terrain processing logic.
