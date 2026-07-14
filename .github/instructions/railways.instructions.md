---
applyTo: "osm2terrn/**/*.py"
---
# Railway Network Rules

## Purpose

Railway systems represent connected transportation networks.

Preserve network structure throughout processing and generation.

---

## Connectivity

Railway networks should:

* preserve connectivity
* preserve navigability
* preserve valid branching structures

Avoid generating disconnected track segments unless explicitly present in source data.

---

## Topology

Preserve:

* node relationships
* segment relationships
* junction structure

Railway processing should maintain valid network topology.

---

## Junctions

Railway branches should connect through valid junctions.

Avoid:

* broken junctions
* duplicate junctions
* disconnected crossings

---

## Segments

Railway segments should:

* form continuous paths
* connect through valid nodes
* maintain source connectivity

Avoid duplicate segments.

---

## Network Design

Treat railways as connected networks rather than isolated geometries.

Prefer modifying existing network structures instead of creating parallel representations.

---

## Validation

Validate:

* connectivity
* topology consistency
* junction integrity
* duplicate nodes
* duplicate segments

Invalid railway structures should fail early.

---

## Generation Rules

Preserve source network behavior whenever possible.

Avoid generating artificial connections not supported by source data.

Keep railway generation deterministic and reproducible.
