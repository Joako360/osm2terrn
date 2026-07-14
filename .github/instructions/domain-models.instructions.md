---
applyTo: "osm2terrn/**/*.py"
---
# Domain Model Rules

## Purpose

Domain models define the internal representation of terrain data.

Use domain models to exchange data between modules.

Avoid passing large unstructured dictionaries between layers.

---

## Architecture

Data Flow:

Acquire
→ Parse
→ Domain Models
→ Processing
→ Exporters

Rules:

* Download modules produce raw data.
* Processing modules produce domain models.
* Exporters consume domain models.
* Exporters must not consume raw OSM data directly.

---

## Model Design

Prefer:

* dataclass(slots=True)
* explicit attributes
* strong typing

Avoid:

* anonymous dictionaries
* nested dictionaries
* dynamic attributes
* loosely typed structures

---

## Core Models

Examples:

* TerrainModel
* HeightmapModel
* RoadModel
* BuildingModel
* RailwayModel

New models should represent a single domain concept.

---

## Relationships

Models may reference other models.

Avoid:

* circular references
* duplicated data
* exporter-specific fields

Store shared information in the most appropriate model.

---

## Coordinate Rules

Domain models use:

* local projected coordinates
* meters for distances
* meters for elevations

Avoid storing latitude/longitude in processed geometry models unless required.

---

## Export Rules

Exporters must:

* read domain models
* transform data into file formats

Exporters must not:

* download data
* parse OSM
* generate domain models

---

## Validation

Domain models should validate:

* required fields
* coordinate consistency
* value ranges when applicable

Invalid data should fail early.

---

## Generation Rules

Prefer extending existing models before creating new ones.

Avoid creating multiple models representing the same concept.

Keep models focused, predictable, and reusable.