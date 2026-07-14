---
applyTo: "osm2terrn/**/*.py"
---
# Performance Rules

## Purpose

Performance should support processing large geographic datasets while preserving correctness, consistency, and terrain quality.

Optimize for scalability rather than premature micro-optimizations.

---

## Scalability

Code should scale from small regions to large geographic areas.

Prefer solutions that remain efficient as dataset size increases.

Avoid algorithms that degrade significantly with large inputs.

---

## Processing

Avoid repeated processing of the same data whenever practical.

Reuse existing computations when possible.

Avoid duplicate processing logic.

---

## Memory Usage

Use memory efficiently.

Avoid:

* unnecessary copies of large datasets
* duplicated geometry storage
* unnecessary intermediate structures

Prefer processing approaches that minimize memory overhead.

---

## Spatial Operations

Prefer efficient spatial operations.

Reuse computed geometries and spatial relationships whenever practical.

Avoid repeatedly performing expensive spatial calculations.

---

## Data Access

Load, transform, and process only the data required for the current task whenever practical.

Avoid unnecessary processing of unused data.

---

## Batch Processing

Prefer batch processing for large datasets when practical.

Avoid excessive per-element processing when equivalent batch operations exist.

---

## Optimization

Optimize only after identifying meaningful bottlenecks.

Favor algorithmic improvements over micro-optimizations.

Performance improvements should not compromise:

* terrain quality
* spatial consistency
* data integrity
* maintainability

---

## Validation

Performance optimizations must preserve:

* deterministic behavior
* output consistency
* processing correctness

Optimized code should produce equivalent results whenever practical.

---

## Generation Rules

Favor scalable and maintainable solutions.

Keep performance improvements predictable and reproducible.

Avoid introducing unnecessary complexity solely for optimization.
