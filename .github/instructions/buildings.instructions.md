---
applyTo: "osm2terrn/**/*.py"
---
# Building Rules

## Purpose

Buildings represent physical structures integrated into the generated terrain.

Building generation should contribute to a coherent and realistic environment.

---

## Placement

Preserve building placement whenever possible.

Buildings should remain spatially consistent with:

* terrain
* roads
* railways
* surrounding structures

Avoid unintended spatial offsets.

---

## Terrain Integration

Buildings should remain consistent with surrounding terrain.

Avoid:

* floating structures
* unintended terrain intersections
* unrealistic placement

---

## Scale

Preserve building scale and proportions whenever practical.

Avoid processing that significantly distorts building dimensions.

---

## Relationships

Preserve relationships between:

* buildings
* roads
* terrain features
* nearby structures

Generated buildings should remain consistent with the surrounding environment.

---

## Simplification

Building simplification is allowed when it improves performance, compatibility, or generation quality.

Preserve the role and overall characteristics of structures whenever possible.

Avoid unnecessary geometric complexity.

---

## Validation

Validate:

* placement consistency
* terrain integration
* duplicate structures
* spatial consistency

Invalid building data should fail early.

---

## Generation Rules

Favor coherent and usable environments over strict preservation of incomplete source data.

Preserve important building characteristics whenever practical.

Keep building generation deterministic and reproducible.

Avoid duplicate building processing logic.
