# Dependency Guidelines

This document defines the dependency policy for **osm2terrn**.

The goal is to keep the project maintainable, reproducible, and easy to contribute to while providing all capabilities required for high-quality terrain generation.

Dependencies should always be intentional. Every package included in the project should provide clear value to the architecture, functionality, or user experience.

---

# General Principles

Dependencies must:

- solve a real problem;
- be actively maintained;
- have a permissive open-source license;
- support Python 3.12 or newer;
- be installable through pip/uv;
- be reasonably cross-platform;
- minimize unnecessary transitive dependencies whenever practical.

Whenever possible, prefer:

- the Python Standard Library;
- existing project code;
- mature scientific Python libraries;

before introducing additional third-party packages.

---

# Dependency Categories

## Core Dependencies

Core dependencies are the libraries required to execute the project or that define the project's intended architecture and capabilities.

A package may be considered a core dependency even if its current usage is limited, provided it represents a planned architectural component or an essential user-facing feature.

Examples include:

- numpy
- scipy
- matplotlib
- Pillow
- networkx
- requests
- osmnx
- geopandas
- shapely
- pyproj
- rasterio
- pyogrio
- rich
- fused
- colorcet
- cmasher
- cmcrameri

These libraries may be imported throughout the project whenever appropriate.

---

## Architectural Dependencies

Some libraries define the long-term direction of the project.

These packages may initially appear in relatively few modules but are considered part of the intended architecture.

Examples:

- fused (Overture Maps support)
- rich (CLI experience)
- colorcet
- cmasher
- cmcrameri

Architectural dependencies are considered **core dependencies** and should not be treated as optional merely because their current usage is limited.

---

## Optional Dependencies

Optional dependencies provide isolated functionality that is not required for standard terrain generation.

Examples include:

- experimental exporters;
- experimental importers;
- benchmarking utilities;
- research prototypes;
- integrations with external software.

Optional dependencies should remain modular and should never be required for the standard terrain generation pipeline.

---

## Development Dependencies

Development dependencies exist exclusively to assist contributors.

These include:

- testing
- linting
- formatting
- static analysis
- IDE integration
- documentation generation
- profiling

Examples:

- pytest
- pytest-cov
- black
- ruff
- mypy
- sphinx
- spyder-kernels
- ipykernel

Development dependencies must never be required at runtime.

---

# Dependency Declaration

The authoritative source for project dependencies is:

```
pyproject.toml
```

Core runtime dependencies belong under:

```
[project.dependencies]
```

Development tools belong under:

```
[project.optional-dependencies.dev]
```

Documentation tools belong under:

```
[project.optional-dependencies.docs]
```

Testing tools belong under:

```
[project.optional-dependencies.test]
```

Compatibility `requirements*.txt` files may exist for convenience or legacy workflows but should not be considered the primary dependency definition.

---

# Dependency Approval

A new dependency should satisfy most of the following:

- actively maintained;
- stable API;
- documented;
- permissive license;
- cross-platform;
- widely adopted;
- significantly reduces implementation complexity;
- provides measurable benefits over custom implementations.

---

# Dependency Rejection

Avoid dependencies that:

- duplicate existing functionality;
- are poorly maintained;
- have very small user communities;
- introduce excessive dependency trees;
- significantly increase installation size;
- require complex native compilation without strong justification;
- only provide cosmetic improvements without improving usability.

---

# Version Policy

Prefer:

- stable releases;
- semantic versioning;
- minimum supported versions.

Avoid pinning exact versions unless strict reproducibility is required.

Prefer:

```text
numpy>=2.0
```

instead of:

```text
numpy==2.0.1
```

Exact versions should instead be recorded in the project's lock file.

---

# Dependency Isolation

Large optional features should isolate their dependencies.

Example:

```
Exporter
└── Optional library
```

instead of importing optional libraries throughout unrelated modules.

Imports for optional functionality should remain as local as practical.

---

# Import Rules

Imports should be grouped in the following order:

1. Python Standard Library
2. Third-party libraries
3. Project modules

Example:

```python
import pathlib

import numpy as np
import rasterio

from osm2terrn import terrain
```

---

# Heavy Dependencies

Large libraries should only be introduced when they provide capabilities that cannot reasonably be implemented using existing project dependencies.

Examples:

- GDAL
- PDAL
- OpenCV
- PyTorch

Such dependencies require explicit architectural justification.

---

# Scientific Libraries

Whenever possible, prefer mature scientific libraries over custom numerical implementations.

Examples include:

- NumPy
- SciPy
- Rasterio
- Shapely
- PyProj

Avoid reimplementing:

- interpolation;
- affine transformations;
- coordinate projections;
- raster operations;
- geometry algorithms.

---

# User Experience Dependencies

Libraries that significantly improve the user experience are encouraged when they remain cleanly separated from business logic.

Examples:

- Rich
- Colorama

These packages may be considered core dependencies when they define the intended user experience of the application.

Business logic should never depend directly on presentation-specific APIs.

---

# Network Dependencies

Online services should remain isolated behind dedicated interfaces.

Current supported providers include:

- OpenStreetMap
- OpenTopoData
- Overture Maps

Network implementations should:

- support configurable timeouts;
- support retries;
- provide informative error messages;
- allow future offline replacements.

---

# Future Dependencies

Future integrations should remain modular.

Possible future packages include:

- GDAL
- PDAL
- OpenCV
- trimesh

Experimental integrations should not become mandatory dependencies until their functionality becomes part of the project's core architecture.

---

# Dependency Auditing

Dependencies should be reviewed periodically.

Candidates for removal include:

- unused packages;
- abandoned libraries;
- duplicated functionality;
- obsolete compatibility layers.

Reducing dependency count while preserving functionality is considered an improvement.

Tools such as:

- deptry
- pipreqs

may be used to periodically audit project dependencies.

---

# Project Philosophy

The project values:

- simplicity;
- modular architecture;
- explicit interfaces;
- stable APIs;
- reproducible environments;
- maintainable code;
- minimal dependency footprint.

Avoid dependency bloat.

Every dependency should earn its place in the project.