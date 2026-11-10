<!-- Author instructions are enclosed in HTML comments. Replace every
     placeholder and remove guidance that does not belong in the finished
     chapter. Keep the section only when marked required or applicable. -->

# <Chapter title>

## Metadata

- ID: `chapter:<stable-slug>`
- Scope: <route, algorithm, or contract studied>
- `inventory_status`: `not_inventoried` | `inventoried` | `excluded`
- `analysis_status`: `not_started` | `static_analyzed` | `human_reviewed` | `blocked`
- `documentation_status`: `not_documented` | `draft` | `reviewed` | `approved`
- `execution_status`: `not_verified` | `passed` | `failed` | `not_applicable`
- Inspected revision/date: <revision or date; state if unavailable>
- Author / reviewer: <names or pending>
- Inventory scope: <file/symbol IDs or paths>

<!-- Required. State the learning boundary and what is intentionally excluded. -->
## Purpose and scope

<Explain the process this chapter studies, its start/end boundary, and exclusions.>

### Learning goals

- <By the end, the reader can ...>

### Prerequisites

- <Knowledge or concepts needed; use None if no special prerequisite.>

### Where this process fits

<Identify its caller/entry and consumer using source evidence. Adapt for a
library algorithm that has no user-facing entry point.>

### Files to study

- `<repository-relative/path.py>::<symbol>` — <role; link the path from the
  chapter when preparing a real chapter.>

<!-- Required when domain concepts are needed. Define terms before use. -->
## Concepts and data contracts

<Explain only concepts required to understand this implementation. Name actual
types, important fields, units/CRS/invariants, and distinctions such as empty,
missing, invalid, or failed where the source makes them.>

## Evidence-based walkthrough

<!-- Required. Follow the actual call/data sequence; adapt subsections to the topic. -->
### Route overview

<Describe the normal source path with narrow locators. Label inferred edges.>

### Component: <class/function/data structure>

- **Purpose:** <why it exists in this route>
- **Inputs:** <actual parameters/config/state and types>
- **Operation:** <key steps/algorithm and transformations>
- **Output or effects:** <return, mutation, persistence, or downstream handoff>
- **Alternatives/errors:** <guards, early returns, exceptions, fallbacks>
- **Evidence and limits:** <claim/evidence IDs and what remains unknown>

<!-- Repeat, combine, or replace this component subsection as appropriate. -->

### Data flow and transformations

<Trace actual values through boundaries. A synthetic example must be labeled
synthetic and must not be presented as captured runtime output.>

### Dependencies and module relationships

<Explain relevant collaborators and distinguish project behavior from library
internals that were not established from source or execution.>

## Branches, errors, and unresolved paths

<Describe meaningful conditions, returns, exception boundaries, and global
outcomes. State static, inferred, test-source, or runtime certainty. Link
tracked open question IDs.>

## Examples

<!-- Recommended. Label each Source-derived, Synthetic, or Execution observation. -->
### <Example title> — <Source-derived | Synthetic | Execution observation>

<Inputs, walkthrough, result, and evidence. For an execution observation,
include its evidence record rather than inventing a result.>

## Diagram references

- `diagram:<slug>` — <relationship type and certainty>; diagram path:
  `diagrams/<file>.mmd` (replace with a real relative link).

<!-- Recommended; required for multi-step or branching flows. -->
## Exercises

### Exercise 1: <title>

- **Objective:** <learning goal>
- **Task:** <what to inspect, derive, or run>
- **Mode:** <static inspection | execution required>
- **Expected check:** <answer or exact symbol/assertion/result to inspect>
- **Evidence boundary:** <what the answer does not prove>

<!-- Repeat per exercise. An execution-required result remains pending until run. -->

## Self-assessment

- <Question testing core concept, data flow, or alternative path>

### Self-assessment guide

- <Concise answer/check guidance; do not fabricate execution output.>

## Limitations and open questions

- `<question-id>` — <what cannot be concluded and evidence needed to close it>

## Claims and evidence

<!-- Required for significant technical assertions. Keep this consistent with
     inventory/claims.jsonl and inventory/schema.json. -->
### Claim: <one checkable statement>

- Claim ID: `claim:<chapter-slug>:<claim-slug>`
- Classification: `fact` | `inference` | `runtime_observation`
- Evidence IDs: `ev:<stable-id>`
- Source locator: `<repository-relative/path.py>::<symbol>` (`#L<start>-L<end>`)
- Limits: <scope, uncertainty, or None known>

## Review record

- Review ID: <review ID or pending>
- Verdict: `pending` | `accepted` | `changes_requested`
- Date: <date or pending>
- Scope and evidence checked: <review summary or pending>
- Remaining findings: <IDs or None>
