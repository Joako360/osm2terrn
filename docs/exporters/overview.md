# Exporters: overview and architecture

## Purpose

Exporter modules generate deterministic, game-ready terrain packages for Rigs of Rods.

## File responsibilities

| File | Responsibility |
|------|----------------|
| `.terrn2` | Terrain entry point, metadata, references |
| `.otc` | Global terrain geometry and rendering config |
| `*-page-X-Y.otc` | Texture layers and blend stacks |
| `.tobj` | Objects, procedural roads, vegetation |

## Core principles

- Separation of concerns between metadata, geometry, textures, and object placement.
- Local origin-centered projected coordinates.
- Meters as canonical units.
- Validate early and fail fast.
