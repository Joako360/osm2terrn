# Coverage and Progress

## Status definitions

Record-level statuses are independent: `inventory_status` is
`not_inventoried`/`inventoried`/`excluded`; `analysis_status` is
`not_started`/`static_analyzed`/`human_reviewed`/`blocked`;
`documentation_status` is `not_documented`/`draft`/`reviewed`/`approved`;
`execution_status` is `not_verified`/`passed`/`failed`/`not_applicable`.
See `inventory/README.md` for meanings and transitions. Generated records are
never marked human-reviewed, editorially approved, or execution-verified.

## Current state

Status snapshot verified against the working tree on 2026-11-07. Historical
sections below retain their original dated findings; where they conflict with
this snapshot or later addenda, use the dated addendum and current source
locators. The generated inventory is a static snapshot and must be regenerated
after source changes.

| Scope | Status | Evidence / limitation | Next action |
|---|---|---|---|
| Initial repository audit | Historical static snapshot | `initial_repository_audit.md`; not a current full inventory | Use `audit_review.md` and refresh evidence during inventory |
| Audit review | Static comparison recorded | `audit_review.md`; discrepancy targets remain open | Recheck each target against current source |
| Book infrastructure | Independent review approved with limitations for functional analysis | `reviews/contract-v3-independent-review.md`; historical `REQUIERE CORRECCIONES` verdicts are preserved. N1-N4 passed this review; execution evidence cannot be authenticated by the validator, and H2-H4 streams remain empty. | Begin static/semantic flow analysis with explicit evidence labels; review execution artifacts before any runtime claim |
| File inventory | Regenerated static snapshot; 2026-11-07 | `inventory/files.jsonl`; `inventory_report.md` | Review classifications/exclusions; generated counts are not completeness |
| Symbol inventory | Regenerated; static AST extraction | `inventory/symbols.jsonl`; 1,007 records in the latest report | Review; module-level variables and dynamic relations may be absent |
| Relations inventory | Regenerated; static extraction | `inventory/relations.jsonl`; 2,505 records and 2,317 unresolved items in the latest report | Review unresolved items; not a complete call/control-flow graph |
| Documentation cross-reference | `not_started` | `inventory/docs_cross_reference.jsonl` intentionally empty | Check documented paths/symbols against source |
| Technical chapters | OSM bbox acquisition pilot `draft`; other candidates `not_started` | `chapters/01-osm-bbox-acquisition.md`; five claims remain `draft` / `not_verified`; independent claim review remains pending | Use the pilot as a method reference under `STYLE_GUIDE.md`; review claims before advancing status |
| Claim/evidence traceability | Five pilot claims recorded as `draft` / `not_verified` | `inventory/claims.jsonl`; source evidence is now symbol/line-located where available; no runtime evidence | Independently verify each claim and its cited locator |
| Control-flow occurrences | Contract ready; no occurrences recorded | `inventory/control_flow.jsonl` empty; no chapter evidence applied; no complete CFG is generated | Record only reviewed source occurrences; do not infer reachability or execution |
| Inventory generator tests | Historical N1-N4 correction tests documented; not rerun in this documentation task | `tests/test_inventory_tool.py`; see historical dated report | Keep tests aligned with schema and discovery changes |
| OSM2Terrn runtime verification | Partial bounded evidence exists; no broad end-to-end or simulator approval | First/second geographic validation reports; second run acquired elevation/assets but OSM layers failed and RoR was not loaded | Treat provider/path results as run-specific; choose safe scoped checks if needed |
| Stage 3 execution-flow reconstruction | Static source map updated; runtime remains partial/unverified by route | `execution/README.md`, `call_paths.md`, `module_map.md`, evidence and validation reports; selected synthetic and geographic runs are separate evidence types | Resolve bbox/elevation/session questions; review static map independently |
| Stage 3.2 download–state–export analysis | Handoff implemented with synthetic coverage; real provider/application behavior not generally verified; bbox and elevation questions remain | `execution/data-handoff-analysis.md`; focused tests are recorded there; `P3-E030`–`P3-E034`; open questions include `question:stage3-state-after-cancel`, `question:stage3-bbox-place-semantics`, `question:stage3-preload-elevation-scope` | Independently review handoff evidence and address separate bbox/state/elevation questions |

**Inventory snapshot — 2026-11-07:** the static inventory
was regenerated from the current working tree: 347 file records (298 included,
49 excluded), 147 Python files parsed, 1,007 symbols, 2,505 relations, 2,317
unresolved items, 47 entry points and 68 dependency records. The validator
passed schema/integrity checks, negative checks, deterministic double
generation, and freshness comparison. `claims.jsonl`, `control_flow.jsonl`
and `docs_cross_reference.jsonl` remain empty by generator design. No
application tests, provider requests or terrain generation were run for this
documentation task. See `progress/inventory_report.md` for the generated
record and `execution/evidence_register.md` for current source findings. This
is the recorded inventory-generation date; it is distinct from any later
documentation-consolidation date. `inventory_report.md` records HEAD and an
input digest but no generated-at timestamp. No evidence in the repository shows
that the inventory was regenerated on 2026-11-09.

**Documentary audit traceability — reviewed 2026-11-09:** a repository search
under `docs/book/` did not find an independent documentary-audit report dated
2026-11-07. The available `audit_review.md` is dated 2026-10-20; it is not the
missing November report. Therefore its specific findings cannot be compared
with this follow-up. This note records the missing artifact and does not
reconstruct or attribute an audit.

The current orchestrator returns `export_outcome=complete` or `partial`.
Uncaught export exceptions are handled by the CLI as an error message and do
not return a global `failed` outcome. `failed` remains a road-stage outcome;
the flow diagram separates those meanings. A failed non-road acquisition layer
is retained as a warning and does not by itself add a global partial reason.

## Chapter readiness — 2026-11-09

The inventory generator and its artifacts were reported as structurally
validated in the 2026-11-07 snapshot. That validation does not satisfy the
pending human semantic review of the file/symbol inventory. The pilot has five
authored records in `claims.jsonl`, but those claims remain draft and have not
been independently reviewed. `control_flow.jsonl` and
`docs_cross_reference.jsonl` remain empty, so they contain no reviewed
control-flow occurrences or generated document-to-code cross-references.

A limited pilot chapter may be prepared as a `draft` after its exact source
scope and evidence are selected. Do not mark any chapter `reviewed` or
`approved`, or its claims technically reviewed, until a human has checked the
relevant code paths, tests/results and limitations and recorded that review.

**Pilot chapter drafted — 2026-11-09:** `chapters/01-osm-bbox-acquisition.md`
documents the current OSM bbox acquisition, per-layer status/cache behavior,
and bounded Overpass wrapper from static source inspection. Its documentation
status is `draft`; inventory and analysis are recorded separately, and
execution remains `not_verified`. The chapter's stable claims and source/test
evidence are recorded in `inventory/claims.jsonl`. Tests are cited as
`test_source`, not as passing test runs; no application, provider, or terrain
execution is claimed. The authored claim stream is preserved by regeneration
after a tooling correction made for this pilot. Review remains pending.

**Pilot checks — 2026-11-09:**

- `python docs\book\inventory\inventory_tool.py generate` completed and
  refreshed the static inventory, including the pilot and diagram
  (`349` file records, `1,008` symbols, `2,507` relations, `2,326` unresolved
  items, `47` entry points, and `68` dependency records).
- `python docs\book\inventory\inventory_tool.py validate` passed schema,
  cross-record, freshness, determinism, and built-in negative self-checks.
- `python -m pytest tests/test_inventory_tool.py::InventorySchemaRegressionTests::test_generation_preserves_authored_claim_records -q`
  could not start because `pytest` is not installed; no dependency was
  installed.
- `python tests\test_inventory_tool.py InventorySchemaRegressionTests.test_generation_preserves_authored_claim_records`
  passed (`Ran 1 test`).
- The chapter's 29 local Markdown links resolved, and `git diff --check`
  exited successfully; Git emitted only line-ending normalization warnings
  for existing workspace files.
- No OSM acquisition tests or application/provider commands were run.

The generated file record for the chapter remains `documentation_status:
not_documented` because static extraction does not advance editorial status;
the chapter and its claims record their current `draft` status directly.

**Pilot correction iteration 2 — 2026-11-09:** the chapter now distinguishes
bbox value validation, CRS metadata and transformation; describes the
potential second reprojection failure before layer handlers; explains the
geometry/network transformations and their returned representations; and
extends the CLI context, cache/error flow, diagram, exercises and symbol/line
evidence. The five claims remain `draft` and `not_verified`; this edit adds no
runtime evidence. The evidence contract now supports optional `symbol_id` and
checks symbol existence, path agreement and line containment. The generator
rejects duplicate JSON object keys before writing artifacts; its previous
always-PASS documentation-contract row was removed. These changes have not
been validated by the inventory tool: the `.venv` Python launcher points to an
unavailable Microsoft Store Python executable, so the documented test,
`py_compile`, and inventory validation commands could not start. No OSM
acquisition tests or application commands were attempted. Inventory artifact
freshness after the tooling/schema change remains unverified; no regeneration
was performed. Git has no tracked baseline for `docs/book/` or these
documentation-tool files in this worktree, so a historical diff cannot be
certified.

**Pilot correction iteration 3 — 2026-11-09:** the chapter and static diagram
now state that manual bbox selection returns an empty place and is rejected by
the current `dlcity()` guard; the unresolved item is product intent. The text
distinguishes caught per-layer cache-write errors from an uncaught whole-bundle
cache-write exception, documents the four-corner bbox reprojection, and
qualifies the nodes-only road result on successful transformation/CRS
validation. A verbatim source excerpt and a clearly synthetic bundle example
were added for study. The five claim IDs and their `draft` / `not_verified`
states were retained. The preservation regression now invokes `generate()`
against a temporary repository root and reads back the emitted `claims.jsonl`.
No tests, inventory validation, application commands, or network operations
were run for this iteration; the revised test is unexecuted. The earlier
recorded one-test pass applies to the previous test body and does not validate
this revision. The worktree remains dirty and the documentation/test paths
remain untracked, so no historical diff is available.

## Street-data contract implementation — 2026-10-20

The Stage 3.2 analysis now contains a proposed acquisition-to-export contract,
comparison of graph/GDF/typed-intermediate alternatives, CRS policy, explicit
absence/error states, and a mock-only test plan. The preferred design is
Option A: preserve the acquired NetworkX graph as canonical and add an explicit
graph-aware adapter/processing handoff plus enough acquisition status to
distinguish not-requested, empty, and failed. The handoff is implemented and
focused synthetic tests passed. The dated implementation record in
`execution/data-handoff-analysis.md` supersedes the earlier proposal status.
This does not verify live provider behavior, a complete interactive
application run, or final simulator output. Separate bbox/state/elevation
questions remain open. See that analysis and `execution/uncertainties.md`.

**P1 follow-up, 2026-10-20:** `tests/test_street_network_integration.py`
(28 offline tests) adds representative synthetic CRS/geometry fixtures and a
mocked `dlcity()` → `export()` → `export_terrain_assets()` integration test.
Focused run: 59 passed, 1 skipped. Still `not_verified`: real provider
payloads, cross-process cache, real elevation/DEM alignment, interactive menu
input, and Rigs of Rods loading. Details: `execution/verification_plan.md`,
`execution/uncertainties.md` (`P3-U015`–`P3-U017`).

**Absent road network, 2026-10-28:** `road_network is None` is not a valid
acquisition outcome (`dlcity()` always stores a `StreetNetworkResult`); with
roads enabled, lost/`missing` results and `not_requested` now yield a partial
export message. Synthetic CLI tests cover each reachable case; focused run:
83 passed, 1 skipped. Details: `execution/verification_plan.md`.

**Closure of P3-U015/U016/U017, 2026-10-27:** a MapData conversion failure now
fails the road stage (`road_mapdata_status=failed`, export `failed`, no
`build_roads_from_graph()` call) while acquisition stays `available`; `empty`
may carry a nodes-only graph with its CRS; the cache algorithm version is `"3"`;
duplicated tests were consolidated. Focused run: 64 passed, 1 skipped. Still
`not_verified`: real provider payloads and their disk-cache round trip, DEM
alignment and Rigs of Rods loading. The later cache/CLI verification added a
two-process pickle round trip for synthetic empty, nodes-only and edged graphs,
confirmed that a version-2 entry is bypassed by the version-3 acquisition
path, and observed CLI warning records and terrain-stage continuation.
The expanded focused run: 66 passed, 1 skipped (114 third-party deprecation
warnings). Details: `execution/verification_plan.md`, `execution/uncertainties.md`.

No percentage or total-coverage claim is made. The historical audit's file
counts and local-directory sizes are snapshot-specific and are not repeated as
current measurements here.

## Recorded offline acquisition/export suites

The following are historical test reports preserved in
`execution/verification_plan.md`. Their execution dates are not recorded in
that document. Neither result was rerun for the 2026-11-09 documentary
correction; the counts come from different commands and scopes.

| Recorded result | Command scope | What it supports | Limits |
|---|---|---|---|
| **106 passed, 1 skipped (93.58s)** | The focused command in `verification_plan.md` includes elevation/heightmap cache, OSM data/loader cache, domain adapters, pipeline state, road export, geometry, street cache process, street-network integration and handoff tests. | Selected synthetic acquisition/export states, cache behavior, output-directory routing, and world-size handoff; named test cases are listed beside the command. | Mocked/offline only; skipped legacy network smoke test; no provider or simulator validation. The execution date is absent. |
| **130 passed, 1 skipped (43.53s)** | A distinct expanded command includes the same main groups plus `tests/test_overpass_retry.py` and `tests/test_config_precedence.py`. | The selected boundaries above plus mocked Overpass retry/failover and configuration validation cases, as described in the later follow-up in `verification_plan.md`. | Mocked/offline only; no live Overpass/provider behavior or simulator validation. The execution date is absent. |
| **2 passed (2.02s)** | Separate `tests/test_otc_exporter.py` command. | Serialized `WorldSizeX/Z` checks recorded in the verification plan. | Does not validate Rigs of Rods interpretation. The execution date is absent. |

These results are historical evidence entries, not a statement of the current
suite status. The algorithm-version/cache and terrain-size limitations in the
detailed verification record remain applicable; real provider payloads, DEM
alignment and simulator loading remain unverified.

## Historical Stage 3 snapshot — 2026-10-20 (superseded where noted)

On 2026-10-20, the declared startup, interactive menu, download, placeholder
load action, and export route were traced from current source. The result is a
static reconstruction, not observed execution. The map separates application
launch candidates from test/tool/script/notebook entry surfaces; their support
status remains unconfirmed where the repository does not establish intent.

Static review identified three consequential code paths: the manual bounding
box selection returns an empty place that the download command rejects; the
elevation preload setting is mapped but is not consulted by that command; and
the current UI export call does not pass its stored OSM bundle into the
`MapData` adapter, whose absent-road input yields an empty road collection.
These are documented observations/inferences from cited source, not fixes or
runtime-confirmed outcomes. See `execution/evidence_register.md` and
`execution/uncertainties.md` for qualifications and exact locators.

The map does not establish provider success, menu reachability, generated
files, supported launcher status, or all notebook/script behavior. No
application tests, network requests, geographic downloads, or terrain
generation were run for this stage. No completeness percentage is claimed.

## Historical Stage 3.2 proposal snapshot — 2026-10-20 (implementation follows)

On 2026-10-20, the area selection, bbox-only downloader, OSM bundle, CLI
session container, elevation acquisition paths, domain `MapData` adapter, road
builder, and output assembly were followed in the current working tree. The
analysis is static. It distinguishes the CLI session class from the separate
domain aggregate and establishes that the downloaded `roads` value is a
locally projected NetworkX graph, while the domain adapter's optional input is
a GeoDataFrame.

Three design decisions remain open: whether bbox-only areas can omit a place
label; what `pipeline.preload_elevation` controls; and whether streets should
come from the downloaded bbox graph or a separate place-based query, including
the appropriate CRS/type contract and `export.include_roads` behavior. No
application code was changed and no tests, requests, downloads, or terrain
generation were run. The detailed evidence and non-executed test plan are in
`execution/data-handoff-analysis.md`.

**Follow-up, 2026-10-20:** the street graph handoff from that analysis has now
been implemented and covered by focused synthetic tests. The preceding
paragraph is the historical analysis snapshot. The current street state and
verification limits are recorded in `execution/data-handoff-analysis.md`;
bbox/state and elevation-preload decisions remain separate and unresolved.

## Update protocol

For each update, identify the file/symbol scope, repository revision or
inspection date, evidence, status, reviewer, and remaining gaps. Record
inventory omissions and extraction failures in the inventory artifact or its
generation report; do not hide them in this summary.

## Seguimiento de corrección N1-N4 — 2026-10-20 (historical)

La implementación amplió el contrato de texto significativo, timestamps UTC,
IDs de revisión Git completos y conteo físico de líneas. Las 19 pruebas del
generador pasaron; `py_compile` pasó; `generate` y `validate --write-report`
validaron los nueve streams, integridad cruzada, negativos, determinismo y
vigencia. El último inventario registra 321 archivos, 784 símbolos, 1.913
relaciones, 1.746 no resueltas, 41 entradas y 62 dependencias. N1-N4 están
corregidos en la implementación y cubiertos por regresiones, a la espera de
la revisión independiente final. No se ejecutó la aplicación ni se verificó el
flujo real de ejecución; H1-H5 no se declaran aprobados en bloque por este
seguimiento. La aprobación se limita a iniciar análisis funcional con los
límites asentados en el informe independiente.

## Chapter documentation standard — 2026-11-09

`STYLE_GUIDE.md`, `WORKFLOW.md`, and the expanded `templates/chapter.md` now
define the reusable writing standard, authoring gates, and chapter scaffold.
`assistant_workflow.md` remains the separate Copilot/Codex coordination
contract. The chapter index records `01-osm-bbox-acquisition.md` as a
methodological reference while preserving its `draft` documentation status and
the five `draft` / `not_verified` claim records. The pilot's structural
conformance snapshot does not replace independent technical review or imply
execution verification. The proposed sequence in `book_plan.md` is a set of
scopes to revalidate against source before drafting, not a confirmed subsystem
architecture. No application code, tests, or claims were changed as part of
this standardization.
