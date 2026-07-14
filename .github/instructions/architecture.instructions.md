---
applyTo: "osm2terrn/**/*.py"
---
# Copilot Instruction: Refactor Project to Remove Redundant Wrapper Modules

## Context

You are working on a Python project that follows a modular architecture. The current codebase contains redundant wrapper modules that only re-export functions or forward imports without adding meaningful abstraction.

Your task is to refactor the project to remove these unnecessary layers while preserving modularity, readability, and functionality.

---

## Goal

Refactor the codebase to:

* Eliminate redundant wrapper modules
* Simplify import paths
* Improve maintainability and navigation
* Preserve the modular architecture

Do NOT change behavior, APIs, or outputs.

---

## Architectural Principles

Follow these rules when analyzing and modifying the code:

### Prefer

* One module = one responsibility
* One package = one domain
* Direct imports between functional modules
* Public APIs exposed via `__init__.py` when appropriate

### Avoid

* Modules that only contain `from x import y`
* Modules that only re-export symbols
* Multi-level forwarding chains
* Empty abstraction layers

---

## Refactoring Rules

### Keep a module if it:

* Contains business logic
* Implements algorithms
* Defines classes or dataclasses
* Defines constants or configuration
* Provides utilities tied to a clear responsibility
* Acts as a meaningful facade over multiple implementations
* Stabilizes a public API

### Remove or merge a module if it:

* Only imports another module
* Only re-exports functions or symbols
* Exists only to rename another module
* Contains no logic beyond forwarding calls
* Adds unnecessary navigation layers

---

## Target Structure

Organize modules by domain. Example:

```
processing/
  terrain/
    heightmap.py
    colormap.py
    splatting.py
    normals.py
    exporter.py

  roads/
    geometry.py
    intersections.py
    procedural.py
    exporter.py

  buildings/
    footprints.py
    exporter.py

  elevation/
    opentopodata.py
    interpolation.py
    filters.py

  osm/
    downloader.py
    parser.py
    cache.py
```

Each module must have a clear and distinct responsibility.

---

## Import Simplification

Replace patterns like:

```
orchestrator -> wrapper.py -> implementation.py
```

with:

```
orchestrator -> implementation.py
```

Only keep wrappers if they provide real abstraction.

---

## Public API Exposure

If a clean API is needed, expose functions via `__init__.py` instead of creating wrapper modules.

Example:

```python
# processing/terrain/__init__.py

from .heightmap import generate_heightmap
from .colormap import generate_colormap

__all__ = [
    "generate_heightmap",
    "generate_colormap",
]
```

---

## File Size Guidelines

* < 100 lines: consider merging if responsibilities overlap
* 200–600 lines: ideal range
* > 700 lines: evaluate for multiple responsibilities

Do NOT split files only to reduce size.

---

## Constraints

Do NOT modify:

* Public behavior
* CLI interfaces
* Tests
* Output formats
* Logging
* Configuration
* External APIs

This is strictly an architectural refactor.

---

## Tasks

1. Identify all wrapper modules
2. Determine if each adds value
3. Remove or merge unnecessary modules
4. Update all imports accordingly
5. Delete obsolete files
6. Maintain clean package structure
7. Ensure all tests pass
8. Apply linting/formatting if configured

---

## Output Requirements

For each change, provide:

* Module removed or modified
* Reason for change
* Updated import paths
* Files affected

At the end, include a summary table:

| Module | Action | Reason |
| ------ | ------ | ------ |

---

## Success Criteria

The refactor is complete when:

* No redundant wrapper modules remain
* The architecture remains modular and clear
* Import paths are simplified
* Each module has a well-defined responsibility
* No functionality has changed
* All tests pass successfully
