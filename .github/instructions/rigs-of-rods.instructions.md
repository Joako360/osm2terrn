---
applyTo: "osm2terrn/**/*.py"
---
# Rigs of Rods Domain Rules

## Purpose

The project generates terrains and related content for Rigs of Rods.

Terrain generation is the primary objective.

All generated systems should contribute to a coherent terrain experience.

---

## Terrain Structure

A terrain may include:

* elevation data
* roads
* railways
* buildings
* objects
* materials

These systems should be treated as parts of a unified terrain.

Avoid treating terrain components as isolated systems.

---

## Consistency

Generated terrain components should remain:

* spatially consistent
* visually consistent
* logically consistent

Preserve relationships between generated features.

---

## Compatibility

Favor simulator compatibility and usability over strict preservation of source data.

Generated content should remain practical for simulation and gameplay.

---

## Scale

Preserve overall terrain scale and proportions.

Avoid introducing features that significantly distort the generated environment.

---

## Integration

Roads, railways, buildings, objects, and terrain features should integrate into a coherent world representation.

Avoid generating conflicting or overlapping terrain systems.

---

## Validation

Validate:

* terrain consistency
* feature alignment
* simulator compatibility

Invalid terrain structures should fail early.

---

## Generation Rules

Favor coherent and usable terrain over strict preservation of incomplete source data.

Preserve important terrain characteristics whenever practical.

Keep generation deterministic and reproducible.

Avoid duplicate terrain generation logic.
