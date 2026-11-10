# Technical Book Plan

## Purpose

Build an evidence-based study book that explains the actual OSM2Terrn
implementation, including entry points, modules, domain types, dependencies,
execution branches, external integrations, and limitations. This plan defines
the work sequence; it does not pre-assert that proposed architecture is
implemented.

## Scope and exclusions

Include only behavior and structures supported by repository evidence. Separate
facts, inferences, and open questions. Cite paths and symbols; use line numbers
as secondary locators.

Do not use this book to:

- change or specify product behavior;
- reproduce secrets, private local data, or generated terrain;
- present a static call graph as observed runtime behavior;
- claim tests pass without recorded execution evidence;
- treat roadmap items, ADRs, or TODOs as implemented features.

## Stages and dependencies

| ID | Stage | Depends on | Status | Exit evidence |
|---|---|---|---|---|
| `stage:1.1` | Initial static repository inspection | None | Audit document exists; historical snapshot | Dated audit with scope and limitations |
| `stage:1.2` | Approve documentary infrastructure specification | `stage:1.1` | Approved specification is present | `codex_especificacion_infraestructura_documental.md` |
| `stage:1.3` | Establish book and inventory infrastructure | `stage:1.2` | In progress until artifacts are reviewed | Linked documents, coherent schema, truthful progress |
| `stage:2` | Generate and validate static inventories | `stage:1.3` | Generated and validated; semantic review remains limited | Reproducible inventories, omissions/failures reported |
| `stage:3` | Reconstruct the actual execution flow from source, then plan bounded runtime checks | `stage:2` | Static map documented; runtime not verified | Entry-point map, per-route call paths, evidence register, open questions, and an explicitly static diagram |
| `stage:4` | Draft technical chapters | `stage:3` | Pilot drafted; next chapters not started | Chapters cite checked evidence, label inferences, and include review records |
| `stage:5` | Review, revise, and publish the book | `stage:4` | Not started | Review record and validated cross-references |

Statuses are not interchangeable: a document existing does not mean its claims
are reviewed, and inventory generation does not mean runtime verification.
Update status only when the corresponding exit evidence exists.

## Chapter planning and proposed sequence

The first pilot exists at `chapters/01-osm-bbox-acquisition.md` and remains a
draft reference. It is not an exhaustive analysis or a technical approval of
the acquisition subsystem. The following order is a planning proposal derived
from the current package tree and Stage 3 source map; each boundary must be
reconfirmed before drafting. A single chapter may combine adjacent topics if
the actual call/data boundaries and learning goals make that clearer.

| Order | Candidate scope | Why it follows here | Current basis / status |
|---|---|---|---|
| 1 | Entry points, CLI/menu, and session state | Gives readers the invocation and state context used by later routes. | `osm2terrn/app/`, `osm2terrn/cli/`; Stage 3 call paths exist. Candidate, not a drafted chapter. |
| 2 | Configuration loading and precedence | Explains how acquisition and processing options reach their consumers. | `osm2terrn/config/`; inspect actual consumers before describing effective behavior. Candidate. |
| 3 | OSM bbox acquisition | Establishes provider requests, layer results, CRS/data transformations, and cache states. | `chapters/01-osm-bbox-acquisition.md`; pilot draft, claims remain draft/not_verified. |
| 4 | Domain types and adapters | Introduces representations and conversion boundaries needed by processing routes. | `osm2terrn/domain/`, `osm2terrn/adapters/`; candidate scope needs human source review. |
| 5 | Elevation acquisition, sampling, and heightmap processing | Builds from geographic inputs and terrain representation toward raster outputs. | `osm2terrn/processing/terrain/`; preparatory source map at `research/02-elevation-processing-research.md`; this is research, not a chapter draft. Consider splitting if code paths differ materially. Candidate. |
| 6 | Road-network processing and export | Depends on graph/domain concepts and follows the implemented street handoff. | `osm2terrn/processing/network/`, `osm2terrn/processing/roads/`; candidate. |
| 7 | Terrain assets, serialization, and export orchestration | Integrates processed resources and output contracts. | `osm2terrn/processing/orchestrator.py`, `processing/otc/`, `processing/terrain/`; candidate. |
| 8 | Cross-cutting tests, evidence, and verification limits | Consolidates what test suites do and do not establish after subsystem chapters exist. | Test tree and `execution/verification_plan.md`; candidate, not a substitute for per-chapter test references. |

This is not a claim that every listed directory forms one subsystem or that
the proposed ordering is mandatory. Review the inventory, call paths, and open
questions before assigning chapter IDs or splitting/combining scopes. Use
`templates/chapter.md` and follow `WORKFLOW.md` for each chapter.

## Diagrams

Diagram topics are not approved as implementation facts in advance. A diagram
may be added only after its relation type and evidence method are known. Follow
`chapters/diagrams/README.md`; static imports/calls, inferred flow, and observed
execution must remain distinct.

## Progress and evidence

- Summary by source file or symbol: `progress/coverage.md`.
- Unresolved questions and closure criteria: `questions/open_questions.md`.
- Documentation decisions: `progress/decisions.md`.
- Inventory contracts and generation state: `inventory/README.md`.
- Independent review process: `reviews/README.md`.

Status snapshot as of 2026-11-09: static inventory streams and a source-based
execution reconstruction exist; selected offline synthetic tests and two
bounded geographic validation reports are documented. These are not exhaustive
semantic inventory, proof of provider reliability, or Rigs of Rods validation.
One technical pilot is drafted and remains pending independent technical and
pedagogical review. See
[`progress/coverage.md`](progress/coverage.md) and
[`execution/README.md`](execution/README.md) for current scope and evidence.
