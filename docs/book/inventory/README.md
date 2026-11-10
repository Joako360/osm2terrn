# Inventory Contract and Generation

## Artifacts

| File | Purpose | State |
|---|---|---|
| `files.jsonl` | Repository file metadata and exclusions | Generated |
| `symbols.jsonl` | Python modules and AST symbols | Generated; static inventory only |
| `relations.jsonl` | Static calls, imports, containment, inheritance, and test references | Generated; resolution is labeled |
| `unresolved.jsonl` | Static references the resolver could not connect | Generated; reasons retained |
| `entry_points.jsonl` | Declared or statically detected execution surfaces | Generated; support status unconfirmed |
| `external_dependencies.jsonl` | Imports compared with declared distributions | Generated; some matches are uncertain |
| `docs_cross_reference.jsonl` | Documented references mapped to source | Empty; later stage; unknown targets may omit `target_path` |
| `control_flow.jsonl` | Explicit static branch and exception occurrences | Empty; AST candidate model, not a full control-flow graph |
| `claims.jsonl` | Stable technical claim IDs linked to evidence IDs | Authored while drafting chapters; preserved by regeneration |
| `generation_report.json` | Input revision/digest, metrics, skipped paths and limits | Generated |
| `schema.json` | Per-record contracts for all nine JSONL streams | Contract version 3 |

The inventory is not a runtime trace, semantic review, or claim of complete
coverage. The cross-reference stream alone is intentionally empty.

## Format and identifiers

- UTF-8 JSONL: one object per non-empty line.
- Paths are repository-relative and use `/` separators.
- File IDs derive from paths; symbol IDs derive from paths and qualified
  names. Line numbers are optional locators, not identity.
- Relation resolution distinguishes `static`, `inferred`,
  `runtime_observed`, and `unresolved`. The generator does not create runtime
  observations because it never executes project code.
- Every record has independent `inventory_status`, `analysis_status`,
  `documentation_status`, and `execution_status` axes. Generation sets
  `inventoried` (or `excluded`), `static_analyzed`, `not_documented`, and
  `not_verified`; it never marks a record reviewed, approved, or executed.
- Status meanings and transition rules are defined below. `passed` or `failed`
  execution requires structured test/runtime evidence.
- Text that carries a reason, description, command, environment, reviewer, or
  test identifier must contain a non-whitespace character. Review IDs use
  `review:<lowercase-hyphenated-slug>`.
- The auxiliary, claim, and control-flow streams have schemas and aggregate
  validation like the file, symbol, and relation streams.
- Every evidence object has a stable `evidence_id` derived from its type,
  repository-relative path, source locator, and description. A claim references
  one or more such IDs; line numbers locate evidence but do not identify it.
- Authored evidence may include `symbol_id`; when present, aggregate validation
  requires that it exists, belongs to the evidence path, and contains the
  cited line range. File path and line checks remain available when no symbol
  can be identified.
- `claims.jsonl` is authored rather than generated. Regeneration preserves
  valid JSONL claim records and stops on malformed JSON instead of replacing
  the stream; validation checks the authored records against the current file
  inventory and schema.

## Work states

| Field | Values | Meaning / permitted progression |
|---|---|---|
| `inventory_status` | `not_inventoried`, `inventoried`, `excluded` | Inventory extraction has not covered the item; a record exists; or the item is recorded but intentionally excluded from ordinary source coverage. Regeneration may move a path between `inventoried` and `excluded`; exclusion needs a reason. |
| `analysis_status` | `not_started`, `static_analyzed`, `human_reviewed`, `blocked` | No analysis; static extraction/inspection recorded; evidence independently reviewed; or a documented blocker. Static analysis may proceed to human review. `blocked` requires a reason in uncertainty/limitations. |
| `documentation_status` | `not_documented`, `draft`, `reviewed`, `approved` | No prose; draft exists; editorial/technical review is recorded; or an explicit approval is recorded. Transitions proceed in order; substantive edits return to `draft`. |
| `execution_status` | `not_verified`, `passed`, `failed`, `not_applicable` | No execution evidence; a specific check passed or failed with command, environment, result, repository revision and date; or execution does not apply. The generator always writes `not_verified`. |

These are independent axes: for example, `static_analyzed` does not imply
`human_reviewed`, `documentation_status=approved`, or `execution_status=passed`.
Do not infer a transition from a generated file's existence.

The aggregate validator enforces these cross-record state rules:

- A file with `inventory_disposition=included` must have
  `inventory_status=inventoried` (or `not_inventoried` while work is pending);
  an excluded disposition must have `inventory_status=excluded`.
- `analysis_status=blocked` requires a non-empty uncertainty or limitation.
- `analysis_status=human_reviewed` and `documentation_status=reviewed` or
  `approved` require inline evidence of type `review`, including a review ID,
  reviewer, UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`), full lowercase Git commit
  object ID (40 or 64 hexadecimal characters) that resolves to a commit in the
  repository, and a passed result. Calendar dates are checked as well as
  timestamp shape. If a verifiable Git revision is unavailable, keep the
  status unverified; do not substitute an arbitrary label. Generated records
  do not carry this evidence and cannot imply human approval.
- `resolution=runtime_observed` requires a passed `runtime_observation` and
  `execution_status=passed` on the same relation. Source evidence alone is not
  execution evidence. Test/runtime evidence requires a meaningful command,
  environment, result, timestamp, and full Git revision; evidence results must
  agree with the record's execution status, and the revision must resolve to
  a commit in the repository. The generator never emits such a relation and
  cannot prove that a supplied command was actually run.
- Located control-flow records require an included source file that is
  available for inspection and a valid one-based line range within that file.
- Physical line counting treats LF, CRLF, and isolated CR as terminators;
  CRLF counts once. An unterminated final line counts once, and an empty file
  has zero addressable lines. Empty Python modules may have null module
  locators, but no located flow/evidence range can point into an empty file.
- `resolved` documentation references require an included target file that is
  available on disk. `unknown`, `unverifiable`, and `expected_missing` remain
  distinct states and do not assert successful resolution.

`schema.json` is a project-specific JSON Schema subset implemented by
`inventory_tool.py`. The validator checks only supported keywords; adding a
schema keyword requires implementation and regression coverage. Aggregate
checks cover ID uniqueness, references, paths, evidence and line ranges.

## Commands

Run from the repository root:

```powershell
python docs/book/inventory/inventory_tool.py generate
python docs/book/inventory/inventory_tool.py validate --write-report
```

The generator uses the Python standard library, reads source as text/bytes for
static analysis, and does not import or run OSM2Terrn modules or access network
services. Validation checks generated and authored records, runs negative
self-checks, compares two in-memory generations, and detects stale generated
artifacts. A PASS applies only to implemented structural checks; it does not
establish semantic completeness or runtime behavior. The Markdown report is
written to `docs/book/progress/inventory_report.md`.

## Discovery and exclusions

Tracked and untracked repository files are considered. Ignored paths are
recorded by category without reading excluded contents. Valid Python files
inside owned code roots are retained even if ignored, unless they are in a
recognized virtual environment, bytecode cache, generated-output or local
private-data directory. The root `/cache/` ignore rule does not ignore the
source package `osm2terrn/cache/`.

Never inventory `.env` values, credentials, tokens, or private local datasets.
Generated terrain, logs, virtual environments, bytecode and tool caches are
excluded from ordinary source analysis.

## Relations and control flow

`relations.jsonl` distinguishes lexical `contains` from `composes` and
`aggregates`. `branches_to`, `raises`, and `handles` are available for
source-supported static relations. All static/inferred edges must use the
matching `resolution`; `runtime_observed` requires runtime evidence and must
never be emitted by the AST collector. Dependency records identify their
internal importing modules with `importing_module_ids`, separate from external
dependency IDs.

`control_flow.jsonl` can record located `conditional_branch`, `match_case`,
`exception_raised`, and `exception_handled` syntax with its condition, exception
type, and handler where applicable. Python AST exposes `If`, `IfExp`, `Match`,
`Raise`, `Try`/`TryStar`, and `ExceptHandler`, so source locations and syntax
can be enumerated statically. The current generator does not populate this
stream. Whether a branch is feasible, an exception escapes, a handler catches
it for a given value, or the code actually executes requires semantic reasoning
or execution. This stream is not a full CFG. Likewise, `composes` and
`aggregates` are available relation kinds but require a reviewed object-lifetime
interpretation; lexical containment alone must not generate them.

## Claim and evidence contract

Each important chapter assertion gets a stable `claim_id` in the form
`claim:<chapter-slug>:<claim-slug>`; do not use a row number that changes when
claims are inserted. `claims.jsonl` records the statement, chapter
path, evidence IDs, statuses, uncertainties, and limitations. Evidence IDs
use `ev:<stable-slug>` for authored evidence; generated static evidence IDs
are deterministic hashes. Evidence types distinguish source, static analysis,
test execution, runtime observation, and documentation. Test/runtime evidence
requires the exact command, test ID when applicable, environment, result,
repository revision, and observation date. The validator checks evidence
references and prevents a passed/failed execution state without matching
execution evidence. Do not manufacture a test record from a test name.

## Documentation references

`docs_cross_reference.jsonl` uses `resolved`, `expected_missing`, `unknown`,
and `unverifiable`. A `resolved` record requires a repository-relative
`target_path` (and an optional valid `target_symbol_id`). Other states omit
`target_path`; if any state supplies `target_symbol_id`, it must identify an
existing inventoried symbol. `original_reference` preserves the text that
prompted the lookup. `expected_missing` means the cited destination should exist but was
not found; `unknown` means the intended destination is not yet known;
`unverifiable` means evidence is insufficient to decide.

## Limits and unresolved cases

AST analysis does not resolve general dynamic dispatch, reflection, all
aliases, plugin loading, environment-dependent branches, or runtime data flow.
Module-level variables/constants are not currently emitted as symbols.
Decorator and base expressions are retained in evidence descriptions rather
than dedicated fields. The relation graph has only local symbol endpoints;
external dependencies are recorded separately. `contains` describes lexical
ownership, not object composition. Branch execution and exception outcomes are
not observed. Keep these limits explicit; do not reduce unresolved counts by
guessing.

The generation report records the inspected Git revision and input digest.
See `../progress/coverage.md` for inventory state and
`../questions/open_questions.md` for unresolved project questions.
