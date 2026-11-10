# Inventory generator audit

**Date:** 2026-10-20  
**Scope:** Static review and regression checks of the documentation inventory generator and its contracts. No OSM2Terrn application workflow, network access, terrain generation, or application test suite was run.

## Decision

**APPROVED WITH DOCUMENTED LIMITATIONS for the initial static-inventory workflow.** The generator now validates all seven JSONL streams, detects malformed inputs without crashing, regenerates deterministically, and has focused regression tests. This approval does not mean that the application has been run, the static call graph is complete, or the technical book is complete. The earlier infrastructure audit's H1–H4 remain open; see `phase-1-4-infrastructure-audit.md`.

## Criteria and evidence

| Criterion | Result | Evidence |
|---|---|---|
| Every JSONL record type has a schema and is validated | Pass | `inventory/schema.json` defines the primary and auxiliary record variants; `inventory/inventory_tool.py:1349` maps all seven streams to schema definitions. The validator output reports every primary and auxiliary record validates. |
| Malformed records and input decoding errors are reported rather than crashing | Pass | `inventory/inventory_tool.py:1326`, `inventory/inventory_tool.py:1349`; regression tests in `../../tests/test_inventory_tool.py:100` and `:116`. Negative self-tests include malformed records and invalid sidecars (`inventory/inventory_tool.py:1477`). |
| Cross-record integrity and generated output are checked | Pass | `inventory/inventory_tool.py:1349` and `:1541`; validation checks references, uniqueness, line ranges, evidence paths, regeneration equality, and deterministic generation. All reported PASS in the run recorded below. |
| Source hidden by a broad ignore pattern remains discoverable, while nested environments are excluded | Pass | `.gitignore:55` anchors `/cache/`; `inventory/inventory_tool.py:227` and `:257` implement collection/exclusion; `../../tests/test_inventory_tool.py:148` checks `osm2terrn/cache/manager.py` and a nested `.venv`. |
| Git rename paths with spaces and modified/deleted/untracked states are handled | Pass | `../../tests/test_inventory_tool.py:167` and `:184`. |
| Generated reports distinguish static inference from runtime evidence | Pass | `inventory/generation_report.json` explicitly states AST-only analysis and limitations; it reports 137 parsed Python files, zero parse failures, 1,449 unresolved call sites, and 74 dynamic constructs. |
| Documentation describes actual paths and current stage | Pass | `inventory/README.md:53` locates the generated Markdown report at `progress/inventory_report.md`; `progress/README.md` documents report ownership. `docs/book/README.md` and inventory README no longer describe the generator/inventories as absent. |
| Open architecture/dependency uncertainties are retained instead of guessed | Pass | `questions/open_questions.md:101` (legacy import roots) and `:117` (YAML dependency declaration). |

## Findings and disposition

### Resolved in this change

- **High — auxiliary record schemas were not enforced.** The previous global validation checked only shared evidence fields for unresolved items, entry points, and external dependencies; deleting required fields or using an invalid support-status enum passed validation. Schema v2 declares all three sidecar contracts, and global validation applies them. Regression cases cover missing fields, invalid enums/classification, broken references, and duplicate IDs.
- **High — malformed data could escape validation or crash the validator.** The current validator reports schema errors before cross-record checks and handles invalid UTF-8 JSONL as a validation error. Focused tests exercise both cases.
- **Medium — ignored source package could be omitted, while broad source-root exemptions risked traversing generated environments.** The root ignore rule is now `/cache/`, and collection preserves the real `osm2terrn/cache/` source while excluding nested environment/cache directories. The test verifies both outcomes.
- **Medium — documentation described obsolete inventory state and omitted the progress index.** The inventory/book READMEs now describe the existing generator, streams, and report location; `progress/README.md` now exists.

### Still open / bounded limitations

- Static call resolution does not infer receiver types and leaves many calls unresolved. The generated report records 1,449 unresolved call sites and describes the causes; this is not evidence of runtime failure.
- No control-flow branch or exception graph is generated. No runtime behavior or tests are represented as verified merely because a test reference or entry point exists.
- Module-level variables/constants are not symbol records; callable references through callbacks, `getattr`, plugins, and environment-dependent behavior are not fully captured. Detailed limits are in `inventory/generation_report.json` and `inventory/README.md`.
- `docs_cross_reference.jsonl` is intentionally empty at this stage. Claim-level chapter-to-symbol evidence and independent inventory/analysis/documentation states are still missing (H1–H4 in the phase 1.4 review).
- The interpretation of legacy import roots (`data`, `processing`, `src`) and whether PyYAML should be a declared direct dependency remain questions; no source code or dependency file was changed.
- The user-listed path `docs/book/inventory/inventory_report.md` does not match the implementation: the generated report is `docs/book/progress/inventory_report.md`. The README now names the observed location.

## Reproduction

Using the bundled Python 3.12.14 runtime:

```text
python docs/book/inventory/inventory_tool.py generate
files=318 symbols=771 relations=1890 unresolved=1539 entries=41 deps=62

python docs/book/inventory/inventory_tool.py validate --write-report
PASS: All JSONL artifacts exist and every non-empty line is a JSON object
PASS: Every primary and auxiliary record validates against schema.json
PASS: Cross-record integrity (unique IDs, references, derived IDs, line ranges, evidence paths)
PASS: Included files exist on disk
PASS: No relation uses resolution 'unresolved' (unresolved items are kept in unresolved.jsonl)
PASS: docs_cross_reference.jsonl is empty (later stage)
PASS: Two consecutive in-memory generations are byte-identical
PASS: Artifacts on disk equal a fresh regeneration (not stale)
PASS: Negative self-tests reject invalid records and broken data sets

python -m unittest discover -s tests -p test_inventory_tool.py -v
Ran 8 tests — OK

python -m py_compile docs/book/inventory/inventory_tool.py tests/test_inventory_tool.py
git diff --check
```

The generator's observed output reported 318 files (274 included, 44 excluded), 771 symbols, 1,890 relations, 1,539 unresolved items, 41 entry points, and 62 dependency records. These counts describe this checkout and generator run only; they do not establish semantic or runtime coverage. The eight unit tests passed. `py_compile` and `git diff --check` completed without errors; Git emitted line-ending warnings for pre-existing changed files.

## Change boundary

The changes for this audit are limited to `.gitignore`, `docs/book/`, and `tests/test_inventory_tool.py`. No application source was edited and no application workflow was executed. The working tree already contained unrelated modifications in application modules and tests, plus untracked `osm2terrn/cache/`; those were preserved. The inventory now includes files observable in the current working tree, so generated counts and git-state fields can change when that tree changes.

## Follow-up — 2026-10-20 — Contract v3

The original approval above applies to the v2 generator at that review date;
its statement that H1–H4 remained open is historical. The v3 follow-up now
records independent inventory/analysis/documentation/execution statuses,
structured test/runtime evidence and claim links, located static control-flow
contracts, external dependency importer-module IDs, and target-optional
documentation references. The generator now writes empty `claims.jsonl` and
`control_flow.jsonl` streams, adds stable IDs to static evidence, and keeps
execution status `not_verified`. On 2026-10-20 the v3 generator produced 320
file records, 776 symbols, 1,897 relations, 1,601 unresolved items, 41 entry
points, and 62 dependency records. The three later-stage streams
(`docs_cross_reference.jsonl`, `control_flow.jsonl`, and `claims.jsonl`) remain
empty by design. The v3 validator reported all nine JSONL streams present,
schema-valid and cross-record consistent, two generations byte-identical, and
on-disk artifacts current; all negative self-checks passed. The focused
unittest suite passed 13 tests; `py_compile` and `git diff --check` completed
successfully. This follow-up does not claim runtime execution or complete
semantic coverage.

## Follow-up — 2026-10-20 — V3-01 to V3-04 correction

The separate contract review found four semantic validation defects after the
v3 checks above. The correction adds state-consistency/review-evidence checks,
requires runtime evidence for `runtime_observed`, validates available line
ranges, and rejects `resolved` references to excluded or unavailable targets.
The latest focused suite passed 18 tests; `py_compile` passed; all nine streams
were regenerated and validated with deterministic/current artifacts. Current
counts are 321 files, 782 symbols, 1,909 relations, 1,699 unresolved items, 41
entry points and 62 dependencies. This update supersedes the earlier v3 test
count and metrics, but not the historical v2 review. Independent re-review is
still pending; the streams for documentation references, control flow and
claims remain empty, so no semantic or runtime coverage is claimed.
