# Module Organization Guidelines

## Purpose

One of the main goals of **osm2terrn** is to remain easy to understand, maintain, and extend as the project grows.

A modular architecture is essential for achieving that goal. However, modularity should never come at the expense of simplicity. Every additional module introduces another place to navigate, another import to maintain, and another level of abstraction to understand.

These guidelines describe how modules should be organized throughout the project and provide the reasoning behind those decisions.

---

# Design Philosophy

This project follows a simple principle:

> **Every module should exist because it has a clear responsibility, not simply because code can be split into another file.**

Splitting code is encouraged when it improves readability, separates concerns, or creates reusable components.

Splitting code is discouraged when it only creates additional navigation without adding meaningful abstraction.

The objective is to keep the architecture both **modular** and **easy to follow**.

---

# Organize by Domain

Packages should represent functional domains of the project.

Examples include:

* `terrain`
* `roads`
* `buildings`
* `vegetation`
* `elevation`
* `osm`
* `export`

Each package groups all functionality related to that domain.

Avoid creating packages whose only purpose is to hold a single forwarding module.

---

# Organize by Responsibility

Inside each package, every module should have one clearly defined responsibility.

Good examples:

```
terrain/
    heightmap.py
    colormap.py
    splatting.py
    normals.py
    exporter.py
```

Each file answers a specific question.

* How is the heightmap generated?
* How are terrain colors generated?
* How are splatmaps generated?
* How are normal maps generated?
* How is terrain exported?

This makes navigation predictable for contributors.

---

# Avoid Redundant Wrapper Modules

A module should not exist solely to forward imports or function calls.

Avoid structures such as:

```
terrain_exporter.py
        │
        ▼
terrain_export_core.py
```

when the first file contains no logic beyond:

```python
from terrain_export_core import export_terrain
```

This type of indirection increases maintenance cost without improving the architecture.

Instead, import the implementation directly.

---

# When a Facade Makes Sense

Not every forwarding layer is unnecessary.

A facade is appropriate when it provides a stable public interface while hiding multiple internal implementations.

For example:

```
roads/

graph.py
graph_builder.py
graph_validation.py
graph_simplification.py
```

If `graph.py` coordinates these internal modules and presents a single public API, it should be preserved.

A facade should simplify the project for its users, not merely redirect imports.

---

# Public APIs

When a package should expose a simplified interface, prefer using the package's `__init__.py`.

For example:

```python
from .heightmap import generate_heightmap
from .colormap import generate_colormap

__all__ = [
    "generate_heightmap",
    "generate_colormap",
]
```

This allows external code to write:

```python
from processing.terrain import generate_heightmap
```

without introducing additional wrapper modules.

---

# File Size

There is no strict maximum file length.

Instead, use responsibility as the primary criterion.

As a general guideline:

* Very small modules (under approximately 100 lines) may indicate unnecessary fragmentation.
* Modules between roughly 200 and 600 lines often represent a healthy level of cohesion.
* Large modules should only be split when they begin to mix unrelated responsibilities.

Never split a module solely to reduce its line count.

---

# Before Creating a New Module

Ask the following questions:

* Does this module represent a distinct responsibility?
* Will contributors naturally look here for this functionality?
* Does this reduce complexity rather than increase it?
* Does it improve readability?
* Is this module likely to grow independently?
* Could the existing module remain clear if this code stayed there?

If the answer to most of these questions is **no**, consider keeping the code in the existing module.

---

# Before Removing a Module

Likewise, ask:

* Does this module provide meaningful abstraction?
* Does it coordinate multiple implementations?
* Does it expose a stable public API?
* Does it hide implementation details?

If none of these apply, the module is probably unnecessary.

---

# Practical Rule

A useful rule of thumb throughout the project is:

> **One package represents a domain. One module represents a responsibility. One function performs one task.**

Following this principle keeps the architecture consistent, predictable, and easy for new contributors to understand.

---

# Goals

These guidelines aim to ensure that the project remains:

* Modular
* Readable
* Easy to navigate
* Easy to extend
* Easy to review
* Easy to maintain

Architecture should help contributors understand the codebase, not require them to navigate through unnecessary layers of indirection.