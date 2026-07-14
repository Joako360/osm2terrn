---
applyTo: "osm2terrn/**/*.py"
---
# Terrain Generation Rules

## Purpose

Terrain generation combines processed geographic data into a coherent terrain representation.

The primary goal is to generate realistic, usable, and internally consistent terrain.

---

## Spatial Consistency

Generated terrain should remain spatially aligned with:

* heightmaps
* road networks
* railway networks
* buildings
* other generated features

Avoid unintended spatial offsets between terrain components.

---

## Integration

Terrain generation integrates multiple terrain-related systems into a unified representation.

Preserve consistency between all generated features.

Avoid generating isolated or conflicting terrain elements.

---

## Terrain Quality

Prioritize:

* terrain realism
* terrain usability
* spatial consistency

Avoid generation artifacts that significantly reduce terrain quality.

---

## Terrain Relationships

Preserve relationships between:

* terrain elevation
* roads
* railways
* buildings
* terrain features

Generated elements should remain consistent with surrounding terrain.

---

## Scale

Preserve overall terrain scale and proportions.

Avoid generation steps that significantly distort spatial relationships.

---

## Validation

Validate:

* spatial consistency
* feature alignment
* terrain coherence
* terrain completeness

Invalid terrain structures should fail early.

---

## Generation Rules

Favor coherent and usable terrain over strict preservation of incomplete source data.

Preserve important terrain characteristics whenever practical.

Keep terrain generation deterministic and reproducible.

Reuse existing terrain generation utilities whenever possible.

Avoid duplicate terrain generation logic.
