# OSM2Terrn Copilot Instructions

## Project

OSM2Terrn generates Rigs of Rods terrains from geographic datasets.

Inputs:

* OpenStreetMap
* OpenTopoData

Outputs:

* terrn2
* tobj
* odef
* heightmaps

Language:

* English only

Python:

* 3.12+

---

## Architecture

Structure:

* data/ → acquisition and parsing
* processing/ → transformation and generation
* utils/ → shared utilities
* scripts/ → automation and examples

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
* Use requirements.txt as the dependency source of truth.
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
