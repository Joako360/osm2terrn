# Safe Verification Plan

This table began as a proposed plan on 2026-10-20. The street-handoff items
and several offline acquisition items were subsequently executed as documented
in the follow-up sections below; their current status is not “proposed”. The
remaining provider/simulator checks are still unverified. Exact historical
test outcomes are retained with their dates and do not imply a rerun in later
documentation work.

No item below was executed as part of the source reconstruction. Sequence the
checks from isolated, non-network paths to controlled integration paths. Do
not run terrain generation or geographic downloads without a separate scope
and cost review.

| Order | Question | Suggested controlled check | Evidence to retain | Does not establish |
|---|---|---|---|---|
| 1 | Which launch commands resolve in the supported installation? | In a clean disposable environment, inspect package installation and run `osm2terrn --help` and `python -m osm2terrn --help`; avoid launching the interactive menu. | Exact commands, Python/package versions, exit codes and stdout/stderr. | Menu actions or provider behavior. |
| 2 | Does config precedence and flag validation match source? | Run focused existing tests `tests/test_cli_config_overrides.py` and `tests/test_config_precedence.py`; add no tests during this stage. | Test command/output, environment and revision; list branches asserted. | Every config-file format/include edge. |
| 3 | Can manual bbox input reach the downloader? | Add a focused test in a later authorized implementation task using a fake renderer and mocked `download_data_from_bbox`; first decide expected semantics for missing `place`. | Input choices and callback arguments; do not call OSMnx. | Live Nominatim/Overpass access. |
| 4 | Is elevation preload actually optional? | In a later fix, use monkeypatch/fake API and assert call count for both config values; inspect test results. | Config value, mocked call count, output state. | OpenTopography service health. |
| 5 | Does download parsing produce expected dict shapes? | Use fixtures for OSMnx feature/network responses and cache hit/miss; test transform, `None` and provider exception branches. | Fixture IDs, assertions and cache state. | Geographic correctness of live queries. |
| 6 | What data reaches export? | Construct synthetic `current_map` input and assert exact arguments to `export_terrain_assets` and `build_mapdata_from_pipeline_context`; decide how roads/buildings are handed off. | Synthetic input, call arguments, resulting MapData IDs. | Terrain visual quality or real provider data. |
| 7 | Do output writers form a consistent package? | With synthetic elevation/MapData and temporary output, mock network/provider boundaries; inspect image dimensions and references among OTC, TOBJ and TERRN2. | File manifest, hashes, parsed references, revision. | Rigs of Rods runtime compatibility. |
| 8 | Do external integration paths work? | Only after prior checks, separately authorize a bounded single-area run with credentials, explicit area, cost limits and output directory. | Real command, environment (redact secrets), revision, logs/output and provider response metadata. | Other areas, all configuration branches, or complete coverage. |
| 9 | Can the acquired graph reach the road exporter without a second query? | After approving the contract, use a synthetic graph and fake elevation/cache boundaries; assert the export processor receives the bundle graph and neither `graph_from_place` nor `graph_from_bbox` is called by the processing stage. | Fixture, call assertions, transformed CRS, temporary `.tobj`, revision and test command. | Provider success or geographic accuracy for real data. |
| 10 | Are empty, missing, failed, and disabled road states distinct? | Mock each acquisition/cache/conversion/export outcome and both `include_roads` values; assert status, diagnostics, warning/skip/fail policy and `roads_exported` metadata. | Case matrix, captured logs and assertions. | Live service availability or complete runtime coverage. |
| 11 | Are CRS transformations correct at every handoff? | Use known synthetic coordinates and explicit source/target CRSs; verify forward/reverse transforms, graph metadata, domain EPSG:4326 input, local AEQD projection, RoR axis inversion, and `target_bounds` compatibility. | Coordinates/tolerances, CRS identifiers, fixture and test output. | Accuracy of all real geographic data or every map extent. |

Never put API keys, tokens, private local paths, or sensitive datasets in the
book. Existing test presence is not test success; record actual results only
after executing the selected test command.

Rows 9–11 were proposed during design; rows 9–10 later received synthetic
coverage, and row 11 was covered only for selected synthetic CRS boundaries.
See the dated follow-ups below for commands/results and remaining limits.

## Street-handoff verification follow-up — 2026-10-20

Rows 9 and 10 received focused synthetic coverage. The executed command was:

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv/Lib/site-packages').Path
python -m pytest tests/test_street_network_handoff.py tests/test_osm_data_handler_cache.py tests/test_osm_loader_cache.py tests/test_domain_adapters_cache.py tests/test_domain_architecture.py tests/test_pipeline_domain_state.py tests/test_road_export.py -q -p no:cacheprovider --tb=short
```

Result: **31 passed, 1 skipped**. The skipped test is the legacy road
integration smoke test that skips network execution. Assertions include
synthetic available/empty/failed/not-requested acquisition outcomes, cache
recovery, graph-to-GDF CRS and attribute preservation, rejected/failed
transforms, the `include_roads` gate, temporary `.tobj` writing, writer error
state, and no place-based reload when a graph is supplied. `py_compile` passed
for the affected application/test modules, and `git diff --check` passed.

This does not establish real-provider CRS metadata or geometry, interactive
reachability, target-bounds compatibility across real extents, elevation
quality, final package correctness, or simulator compatibility. No live
service, download, or terrain-generation path was run. Rows 1–8 and the
uncovered portions of row 11 remain future work.

## P1 integration tests — 2026-10-20

Added `tests/test_street_network_integration.py` (28 offline tests) after the
independent review (`APPROVED WITH LIMITATIONS`). Command and result:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_street_network_integration.py tests/test_street_network_handoff.py tests/test_osm_data_handler_cache.py tests/test_osm_loader_cache.py tests/test_domain_adapters_cache.py tests/test_domain_architecture.py tests/test_pipeline_domain_state.py tests/test_road_export.py -q -p no:cacheprovider --tb=short
```

Result: **59 passed, 1 skipped** (the skipped test is the legacy network smoke
test). The new file alone: 28 passed; two of its tests run alone also passed.

| Property | Status |
|---|---|
| Verified before (31 tests) | Acquisition states, cache recovery, CRS validation, basic graph→GDF→MapData, `include_roads` gate, writer failure, no place reload for a supplied graph. |
| Verified now (synthetic, offline) | Projected (EPSG:32721, EPSG:3857) and geographic graphs are transformed (coordinates compared with an independent `pyproj` transform, not just labelled); acquisition output is local AEQD and round-trips to EPSG:4326 within 1e-6°; provider and canonical graphs are not mutated (full snapshot comparison); edges without geometry become a node-to-node line; missing endpoint coordinates raise; `MultiLineString` is preserved and split into domain roads; null optional attributes keep the edge; edgeless graph gives an empty EPSG:4326 frame; missing/invalid CRS and transform failure surface as `failed` (acquisition) or exceptions (adapter), never `empty`; non-4326 input to MapData is rejected; real `dlcity()` → `export()` → `export_terrain_assets()` passes the identical `StreetNetworkResult` and graph object to `build_roads_from_graph`, with one mocked provider call and zero reloads; failure/empty/`include_roads=False`/conversion-failure/cancel paths. |
| Pending (real data) | Real OSMnx/Overpass payloads and CRS metadata, real multipart/attribute shapes, cross-process cache round-trip, real elevation/DEM alignment, target-bounds on real extents. |
| Pending (Rigs of Rods) | Loading the generated `.terrn2`/`.tobj` and road placement in the simulator. |

Limits: `download_menu`, the heightmap fetch and all providers are mocked, so
menu interaction and real elevation preload are not covered. Tests do not
prove behavior that is not asserted; no mutation testing was run, so their
sensitivity to a reintroduced defect is argued from the assertions only.

## Contract closure — 2026-10-27 (P3-U015, P3-U016, P3-U017)

Production changes: `osm2terrn/processing/orchestrator.py` (conversion failure
no longer rewrites acquisition status; adds `road_mapdata_diagnostic`;
`_export_roads` fails the road stage without calling `build_roads_from_graph()`),
`osm2terrn/data/street_network.py` (`empty` may carry a nodes-only graph with a
matching CRS), `osm2terrn/data/osm_data_handler.py` (keeps nodes-only graphs;
`_OSM_BBOX_ALGORITHM_VERSION` `"2"` → `"3"`). Tests changed:
`tests/test_street_network_integration.py` (the old conversion-failure
characterization test was replaced by the new policy, not weakened; five tests
added) and `tests/test_street_network_handoff.py` (duplicates removed).

Command (same focused set as above) and result:
**64 passed, 1 skipped** (skipped: legacy network smoke test). The first run after
the contract-test edit used `nx.MultiDiGraph([(1, 2)])` while expecting the
missing-CRS validation message. That fixture contains one edge, and
`StreetNetworkResult` correctly rejects an `empty` result with edges before
checking its CRS; this explains that failure. A later repeat was launched
alongside the fixture edit and reported the same old validation message even
though the displayed source had changed. That concurrent repeat was not
reproduced in isolation or in the full focused run; its exact cause is
unresolved. No bytecode or concurrency explanation is asserted.

| Property | Status |
|---|---|
| Verified now (synthetic) | Conversion failure → acquisition `available`, mapdata `failed` with diagnostic, export `failed`, no `.tobj` builder call, terrain stages still run; invalid result stays an acquisition failure; no-node graph → `empty` with `graph=None`; nodes-only graph → `empty` with nodes and CRS retained; nodes-only without CRS → `failed`; `validate()` rejects invalid status/graph/CRS combinations; memory-cache round trip keeps the nodes-only result with `source="cache"`; cache version is `"3"`. |
| Not verified | Behavior of a real cache directory across processes, including old-version entries on disk (only key separation by version is argued, not run); real providers returning nodes-only graphs; real DEM alignment. |
| Pending (Rigs of Rods) | Loading generated `.terrn2`/`.tobj` in the simulator. |

## Final cache and CLI verification — 2026-10-27

The process-isolated checks use pytest's unique `tmp_path` cache directories;
they do not read or clear the user's configured cache.

Specific command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_street_cache_process.py tests/test_street_network_integration.py -q -p no:cacheprovider --tb=short -W ignore -k "street_network_result_persists_between_processes or algorithm_version_three_does_not_reuse_version_two_bundle or mapdata_conversion_failure_fails_roads_globally_but_keeps_terrain_stages or street_result_contract_for_empty_with_graph"
```

Result: **4 passed, 31 deselected**. One process wrote `StreetNetworkResult`
objects for a graph with no nodes, a nodes-only graph, and a graph with edges
using `FileCacheBackend`/pickle; a second process restored and validated all
three, including node and edge attributes. The test asserts that the process
IDs differ. The version test writes an empty bundle under the application
algorithm version `"2"` and then calls `download_data_from_bbox()` with the
current version `"3"`; the mocked provider is called once and its nodes-only
graph is returned with `source="query"`, proving the old key was not reused.

Focused-suite command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_street_cache_process.py tests/test_street_network_integration.py tests/test_street_network_handoff.py tests/test_osm_data_handler_cache.py tests/test_osm_loader_cache.py tests/test_domain_adapters_cache.py tests/test_domain_architecture.py tests/test_pipeline_domain_state.py tests/test_road_export.py -q -p no:cacheprovider --tb=short
```

Result: **66 passed, 1 skipped, 114 warnings**. The warnings are
`MatplotlibDeprecationWarning` messages emitted by `cmasher` for passing `N` to
`ListedColormap`; the skipped test is the legacy network smoke test.

The mocked CLI conversion-failure test observes `commands.export()` returning
`None`, the road failure statuses in `MapData.metadata`, warning records for
the conversion and skipped `.tobj`, and execution of the independent terrain
export stages. At that point the CLI still printed the general “Export
complete” message; this was corrected on 2026-10-27 (see below).
`utils.logger` configures a console `StreamHandler`; this verifies the
non-interactive command path, not a manual terminal session or process exit
code.

The earlier malformed-fixture test passes in isolation now. Live provider
payloads, real OSM data in a disk-cache round trip, DEM alignment, and simulator
loading remain unverified.

## Partial-export reporting — 2026-10-27

Change: `export_terrain_assets()` adds a `roads_outcome` key (`failed` when
`road_export_status=failed` or `road_acquisition_status=failed`; otherwise the
export status or `disabled`) via `_roads_outcome()` in
`osm2terrn/processing/orchestrator.py`; `commands.export()` in
`osm2terrn/cli/commands.py` prints a "Partial export" message and a warning
log when it is `failed`, and still prints "Export complete" otherwise. The
only in-repo consumer of the returned dictionary is `commands.export()`;
`export()` itself still returns `None`. Acquisition, MapData and export
statuses in metadata are unchanged.

Command (same focused set as above) and result: **77 passed, 1 skipped**;
`git diff --check` exited 0 (it printed only pre-existing LF/CRLF warnings).

| Verified (synthetic, mocked CLI) | Success → "Export complete"; MapData conversion failure and acquisition failure → partial message, no "Export complete", `.tobj` builder not called; valid empty/nodes-only graph and `include_roads=False` → "Export complete"; mandatory terrain stage failure → "Error during export" only; `roads_outcome` mapping; no contradiction between log, metadata and printed message in these cases. |
|---|---|
| Not verified | Real terminal rendering, process exit code (still 0-equivalent: `export()` does not raise on partial export), real providers. |

## Offline acquisition, export path, and scale follow-up

Focused command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_elevation_cache.py tests/test_heightmap_cache.py tests/test_osm_data_handler_cache.py tests/test_osm_loader_cache.py tests/test_domain_adapters_cache.py tests/test_domain_architecture.py tests/test_pipeline_domain_state.py tests/test_road_export.py tests/test_geometry_utils.py tests/test_street_cache_process.py tests/test_street_network_integration.py tests/test_street_network_handoff.py -q -p no:cacheprovider --tb=short -W ignore
```

Recorded historical result: **106 passed, 1 skipped in 93.58s**. The execution
date was not recorded. The command above covers the listed cache, domain,
pipeline, geometry, road, and street-network tests; it does not include the
later Overpass retry or config-precedence test modules. The skipped case is the
legacy network smoke test. It uses synthetic data and mocks; it does not
contact providers or generate terrain. This result was not rerun for the
2026-11-09 documentation correction.

| Verified | Evidence |
|---|---|
| Legitimate empty geometry is distinct from acquisition failure and can be cached | `test_legitimate_empty_geometry_is_cached_with_empty_status`, `test_osmnx_no_matching_features_is_a_valid_empty_result` |
| Mocked HTTP 502/401 failures are classified, not cached as successful bundles, and a later successful retry is cached | `test_failed_geometry_is_not_cached_and_can_be_retried` |
| A legacy algorithm-4/format-2 entry is not reused by algorithm 5 | `test_version_five_does_not_reuse_legacy_bundle` |
| The road writer uses the configured output directory from a different CWD; the place-based API forwards an explicit directory | `test_graph_road_builder_uses_configured_output_from_another_working_directory`, `test_place_road_builder_forwards_configured_output_dir` |
| Current bbox/world-size calculation is characterized, including the former second-round-up measurement | `test_validation_bounds_measurement_exposes_second_world_size_round_up` |
| CLI export preserves the initial 2048 m world size rather than recomputing 4096 from the geographic square envelope | `test_cli_preserves_initial_world_size_through_export` |

Complementary writer command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_otc_exporter.py -q -p no:cacheprovider --tb=short -W ignore
```

Recorded historical result: **2 passed in 2.02s**; the tests verify the emitted
horizontal `WorldSizeX/Z` values. The execution date was not recorded; this is
not a Rigs of Rods compatibility check and was not rerun for the
2026-11-09 documentation correction.

`git diff --check` exited 0 after the update; Git emitted only LF/CRLF
conversion warnings for existing working-tree files. The documentation folder
is untracked in this worktree, so its whitespace was checked separately.
Not verified: live provider errors or payloads, actual configured-user output
paths, Rigs of Rods interpretation of `WorldSize`, road-DEM coverage at the
geographic boundary, and simulator loading. No real geographic export was
rerun after the world-size handoff change.

## Absent road network contract — 2026-10-28

Static finding: `download_data_from_bbox()` always sets `data["roads"]` to a
`StreetNetworkResult` (`not_requested` when `roads` is not in
`osm_data_handler.networks`, `failed` on exception, otherwise
`available`/`empty`). `road_network=None` therefore is never a valid
acquisition outcome; it only arises when `current_map.data` lacks or loses
`roads` (state loss) or when `export_terrain_assets()` is called directly
without it. `StreetNetworkResult(status="missing")` is not produced by any
acquisition path found; it is only handled defensively.

Change (`_roads_outcome()` in `osm2terrn/processing/orchestrator.py`,
`export()` in `osm2terrn/cli/commands.py`): with roads enabled,
`road_acquisition_status` of `missing` (including `road_network is None`) now
gives `roads_outcome=failed`; `not_requested` gives `roads_outcome=not_requested`.
Both print "Partial export" and a warning (with a distinct reason) instead of
"Export complete". `disabled`, `empty`/nodes-only, `available` are unchanged.
Metadata statuses are unchanged and `build_roads_from_graph()` is not called.
The process exit code is unchanged.

Command (same focused set) and result: **83 passed, 1 skipped**;
`git diff --check` exited 0 (apart from pre-existing LF/CRLF warnings).

| Case | Status |
|---|---|
| Roads disabled (also with a lost result) → "Export complete" | Verified (synthetic) |
| Not requested by network config → partial, reason shown | Verified (synthetic) |
| Acquisition failed → partial | Verified (synthetic) |
| `roads` absent or `None` in session data → partial, no `.tobj` build | Verified (synthetic) |
| Valid empty / nodes-only → "Export complete" | Verified (synthetic) |
| `missing` status mapping | Verified at `_roads_outcome()` only; unreachable via acquisition |
| Real providers, terminal rendering, exit code | Not verified |

## Bounded Overpass retries and partial layer cache

The bbox acquisition path now retries temporary HTTP statuses (408, 425, 429,
and 5xx), request timeouts, and connection errors, up to three attempts and
120 seconds per layer by default. It uses exponential full jitter from 1 to 30
seconds and honors `Retry-After` when the requested delay fits the remaining
time budget. Permanent 4xx responses are not retried. The OSMnx 2.1.0 internal
429/504 recursive retry is intercepted so it does not add a separate,
unbounded retry loop.

`OVERPASS_URL` selects the primary endpoint;
`OVERPASS_ALTERNATE_URLS` accepts comma-separated alternatives.
`OVERPASS_MAX_ATTEMPTS` and `OVERPASS_MAX_ELAPSED_SECONDS` configure per-layer
limits. Endpoint values must be HTTP(S) URLs without credentials, query
parameters, or fragments. Retry diagnostics include only the status code or
exception type, not request URLs.

Successful and valid-empty layers are cached independently. A failed layer is
not stored as an empty result, and a later run can reuse earlier successful
layers while retrying the failed one. The existing complete-bundle cache
format remains readable; per-layer entries are separately versioned and tied
to the bbox algorithm version.

Focused offline command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_elevation_cache.py tests\test_heightmap_cache.py tests\test_osm_data_handler_cache.py tests\test_osm_loader_cache.py tests\test_domain_adapters_cache.py tests\test_domain_architecture.py tests\test_pipeline_domain_state.py tests\test_road_export.py tests\test_geometry_utils.py tests\test_street_cache_process.py tests\test_street_network_integration.py tests\test_street_network_handoff.py tests\test_overpass_retry.py tests\test_config_precedence.py -q -p no:cacheprovider --tb=short -W ignore
```

Recorded historical result: **130 passed, 1 skipped in 43.53s**. The execution
date was not recorded. This is a distinct expanded command: compared with the
106-test command above, it additionally includes
`tests/test_overpass_retry.py` and `tests/test_config_precedence.py`. Mocks
cover HTTP 429/502/503/504,
timeouts, connection errors, permanent responses, attempt limits, jitter,
`Retry-After`, endpoint failover, OSMnx's internal-retry interception,
configuration validation, safe diagnostics, partial layer caching, cache
reuse, road failure diagnostics, and legacy cache behavior. It was not rerun
for the 2026-11-09 documentation correction. `git diff --check` is a separate
working-tree check, not a test result.

Not verified: live Overpass availability, endpoint-specific `Retry-After`
behavior, real provider responses, and timing under actual network latency.
No HTTP requests or geographic validation were performed for this change.
