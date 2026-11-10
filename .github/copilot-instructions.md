# OSM2Terrn Copilot Instructions

## Project

OSM2Terrn generates Rigs of Rods terrains from geographic datasets.

Inputs and integrations observed in source include OpenStreetMap through
OSMnx/Overpass, elevation through the OpenTopography service, and a separate
Fused/Overture buildings callable. Do not assume each integration is part of
the default interactive route or that a provider call succeeds.

Outputs:

* terrn2
* otc
* tobj
* PNG terrain rasters

Language:

* English only

Python:

* 3.12+

---

## Architecture

Current package areas are `osm2terrn/app/`, `cli/`, `config/`, `data/`,
`domain/`, `processing/`, `output/` and `utils/`. Inspect the current tree
before adding modules; the architecture guide is a source-linked summary.

Rules:

* Keep acquisition, processing, and export logic separated.
* Prefer extending existing modules before creating new ones.
* Avoid cross-layer dependencies.
* Avoid monolithic files and oversized functions.

---

## Spatial Rules

* BBox is the source of truth for spatial bounds.
* Use coordinate_transform for coordinate conversion.
* Prefer local projected coordinates during processing.

---

## Logging

* Use utils.logger.
* Avoid print().
* Log important operations, warnings, and recoverable errors.

---

## Dependencies

* Prefer existing project dependencies.
* Use `pyproject.toml` as the declared dependency source of truth.
* Suggest new libraries only when clearly justified.

---

## Code Standards

* Follow PEP8 and PEP257.
* Use type hints.
* Use pathlib instead of os.path.
* Prefer dataclasses for structured models.
* Prefer composition over inheritance.
* Raise specific exceptions.
* Avoid bare except blocks.
* Prefer explicit and readable code.

---

## Repository Awareness

Before generating code:

* Reuse existing modules and utilities.
* Follow existing naming conventions.
* Search for similar implementations before creating new ones.

When modifying code:

* Preserve public APIs unless explicitly requested otherwise.
* Minimize unrelated changes.

---

## Data Flow

Preferred pipeline:

Acquire → Parse → Transform → Generate → Export

Rules:

* Processing produces domain models.
* Exporters consume domain models.
* Avoid passing raw OSM data directly into exporters.

---

## Generation Rules

Always:

* Generate complete implementations.
* Include docstrings for public APIs.
* Include type hints.
* Produce production-ready code.

Avoid:

* TODO placeholders.
* Pseudocode.
* Duplicate implementations.
* Global mutable state.

---

## Additional Instructions

* Documentation: `.github/instructions/docs.instructions.md`
* Exporters: `.github/instructions/exporters.instructions.md`

File-specific instructions override this document.
