---
applyTo: "osm2terrn/**/*.py"
---
# GIS Rules

## Coordinate Systems

Geographic coordinates:

* Use for data acquisition and storage when required.

Projected coordinates:

* Use for processing, measurements, and generation.

Do not mix coordinate systems within the same operation.

---

## Units

Distances:

* meters

Elevations:

* meters

Areas:

* square meters

Angles:

* degrees unless otherwise specified

---

## Geometry

Prefer geometry objects over raw coordinate arrays.

Validate geometries before processing.

Fail early on invalid geometries.

---

## Spatial Extents

BBox is the source of truth for spatial bounds.

Use BBox for:

* validation
* clipping
* extent calculations

---

## Measurements

Perform measurements using projected coordinates.

Avoid:

* distance calculations in geographic coordinates
* area calculations in geographic coordinates
* mixing meters and degrees

---

## Data Flow

Acquire
→ Transform Coordinates
→ Process
→ Generate
→ Export

Processing stages should operate on a consistent coordinate system.

---

## Validation

Validate:

* coordinate consistency
* geometry validity
* spatial bounds

Invalid spatial data should fail early.

---

## Generation Rules

Prefer existing coordinate transformation utilities.

Avoid duplicate transformation logic.

Keep GIS operations deterministic and reproducible.