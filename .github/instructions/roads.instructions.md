---
applyTo: "osm2terrn/**/*.py"
---
# Road Network Rules

## Purpose

Road systems represent connected transportation networks.

Preserve network structure throughout processing and generation.

---

## Connectivity

Road networks should:

* preserve connectivity
* preserve intersections
* preserve navigability

Avoid generating disconnected segments unless explicitly present in the source data.

---

## Topology

Preserve:

* node relationships
* segment relationships
* intersection structure

Road processing should maintain valid network topology.

---

## Intersections

Intersecting roads should share common nodes.

Avoid:

* duplicate intersections
* overlapping disconnected crossings
* broken junctions

---

## Segments

Road segments should:

* form continuous paths
* connect through valid nodes
* maintain source connectivity

Avoid duplicate segments.

---

## Network Design

Treat roads as a connected network rather than isolated geometries.

Prefer modifying existing network structures instead of creating parallel representations.

---

## Validation

Validate:

* connectivity
* topology consistency
* intersection integrity
* duplicate nodes
* duplicate segments

Invalid network structures should fail early.

---

## Generation Rules

Preserve source network behavior whenever possible.

Avoid generating artificial connections not supported by source data.

Keep road generation deterministic and reproducible.
