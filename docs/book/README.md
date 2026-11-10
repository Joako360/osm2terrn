# Technical Book Workspace

This directory contains the planning, evidence, inventory contracts, and
coordination materials for the OSM2Terrn technical book. It is not itself a
chapter and does not replace the project's existing contributor documentation.

## Sources of truth

- The current repository tree and cited source files are the evidence for
  implementation facts.
- `initial_repository_audit.md` is a historical static snapshot. Read
  `audit_review.md` for its comparison with the tree inspected on 2026-10-20.
- `codex_especificacion_infraestructura_documental.md` is the approved
  infrastructure specification for this setup.
- `inventory/schema.json` defines JSONL contracts. Static inventory streams
  are generated; `control_flow.jsonl` and `docs_cross_reference.jsonl` remain
  empty until evidence is recorded. `claims.jsonl` contains authored pilot
  claims; consult its records and statuses.
- `progress/coverage.md`, `questions/open_questions.md`, and
  `progress/decisions.md` track status, unresolved questions, and documentation
  decisions. Do not treat planned work as evidence.

If sources conflict, cite the conflicting versions and record the discrepancy;
do not silently rewrite historical evidence or infer runtime behavior from
static structure.

## Structure

- `book_plan.md`: scope, sequence, dependencies, and current stage status.
- `assistant_workflow.md`: Copilot/Codex responsibilities and handoff rules.
- `STYLE_GUIDE.md`: reusable writing, evidence, pedagogy, and diagram standard.
- `WORKFLOW.md`: authoring and independent-review gates for each chapter.
- `audit_review.md`: dated review of the initial audit against the current tree.
- `inventory/`: schema and generated JSONL inventory artifacts.
- `progress/`: coverage summary and documentation decisions.
- `questions/`: questions with evidence and closure conditions.
- `research/`: preparatory subsystem investigations; these are not chapters or
  execution reports.
- `chapters/`: chapter drafts, index, and diagram conventions.
- `execution/`: Stage 3 source-based execution map, call paths, module
  boundaries, evidence register, uncertainties, verification plan, and Mermaid
  flow diagram. The map itself is source-based; bounded runs are recorded in
  separate validation reports and do not establish general provider behavior.
- `reviews/`: independent review process.
- `templates/`: canonical chapter, review, and handoff templates.

## Inventory and regeneration

JSONL inventories use one JSON object per non-empty line, with repository-
relative paths. `inventory/inventory_tool.py` provides deterministic static
generation and structural validation. It does not execute application code;
its reports label unresolved cases and analysis limits. See
`inventory/README.md` for commands and the scope of its validator. Do not
interpret a PASS as semantic or runtime verification.

## Exclusions and sensitive data

Exclude virtual environments, caches, logs, generated terrain/output, compiled
Python artifacts, and large local datasets from ordinary source inventory.
Record exclusion categories and reasons without reading or copying private
contents. Never record secret values. Environment-variable names may be
included when relevant; `.env` contents must not be inventoried.

## Evidence and status

Use repository-relative paths in records. Include symbol identifiers where
available and line numbers only as locating aids. Distinguish static facts,
inferences, unresolved references, and runtime observations. A test reference
does not mean that test passed. Execution status is independent of inventory,
analysis and documentation; passed/failed requires structured command,
environment, result, revision and observation date.

Status meanings and the current state are summarized in
`progress/coverage.md`. Copilot/Codex coordination is in
`assistant_workflow.md`; chapter authoring uses `WORKFLOW.md` and
`STYLE_GUIDE.md`.

The current source-based execution reconstruction is indexed in
`execution/README.md`. Its findings are not application fixes or runtime
verification. Selected synthetic tests and bounded geographic validation runs
are recorded separately; they do not establish general provider behavior or
Rigs of Rods compatibility. One pilot chapter is a `draft` method reference;
other candidate chapters remain `not_started`, and the pilot's claims have not
been independently approved or verified in execution. See
`progress/coverage.md` for dated status and limitations.
