# Uncertainties and Findings — Stage 3

This list separates code facts requiring follow-up from questions that source
inspection alone cannot answer. It does not change application code.

## Status follow-up — 2026-11-07

The table retains original finding language. Current status supersedes those
rows where newer source or synthetic evidence exists:

- `P3-F003`, `P3-F004`, and the pre-change road portion of `P3-F005` are
  historical findings addressed by the explicit street graph handoff and
  `export.include_roads` gate. See `data-handoff-analysis.md` and
  `P3-E030`–`P3-E034` in `evidence_register.md`. This is synthetic/source
  evidence, not live-provider, full interactive, or simulator validation.
- `P3-F001` (manual bbox rejected by place-label guard) and `P3-F002`
  (preload flag not consulted by `dlcity`) remain current source findings.
- Provider availability, actual response payloads, DEM alignment, final
  output validity and Rigs of Rods loading remain unverified unless a dated
  validation report explicitly records a bounded observation.
- Historical per-test counts and run outcomes below are not a claim that tests
  were rerun during the 2026-11-07 documentation consolidation.

| ID | Kind / status | Item | Evidence / next evidence needed |
|---|---|---|---|
| `P3-U001` | Documentation discrepancy; code fact | Root README's `python main.py` does not match the current root file set. | `README.md:78-85`; `pyproject.toml:105-106`; `osm2terrn/__main__.py:1-3`. Clarify which entry command maintainers support. |
| `P3-U002` | Candidate not executed | Direct `python osm2terrn/app/main.py` has a main guard, but launch support/import resolution is not verified. | `osm2terrn/app/main.py:1-16,184-185`; verify only in a controlled environment later. |
| `P3-U003` | Candidate not executed | `start.bat` assumes a Windows `.venv` interpreter path and pauses. | `start.bat:1-2`; confirm packaging/setup and user-facing support. |
| `P3-F001` | Static code finding | Custom bbox returns an empty place string that the next `dlcity` guard rejects. | `osm2terrn/data/download_menu.py:48-49`; `osm2terrn/cli/commands.py:27-35`. No runtime interaction tested. |
| `P3-F002` | Static code finding | `pipeline.preload_elevation` is exposed and configurable but not read before the unconditional prefetch in `dlcity`. | `osm2terrn/app/main.py:56,142-150`; `osm2terrn/config/models.py:201,272-273`; `osm2terrn/cli/commands.py:65-79`. |
| `P3-F003` | Static data-flow finding | Downloaded OSM bundle remains in `current_map.data`; export receives bounds/elevation/place/origin but not the bundle/roads GeoDataFrame. The adapter called by the orchestrator makes `roads=[]` without `roads_gdf`, so `_export_roads` skips that route. | `osm2terrn/cli/commands.py:32-109`; `osm2terrn/processing/orchestrator.py:187-205`; `osm2terrn/domain/adapters/osmnx_to_map.py:54-105`; `osm2terrn/processing/orchestrator.py:151-185`. Follow the intended handoff before asserting road export. |
| `P3-U004` | Runtime unresolved | Whether OSMnx queries return data, cache hit/miss behavior, and provider error paths under configured environment. | Code references `osm2terrn/data/osm_data_handler.py:56-169`; requires controlled provider mocks or explicitly approved external check. |
| `P3-U005` | Runtime unresolved | Whether OpenTopography credential, endpoint, DEM response and raster decode succeed; fallback branch behavior. | `osm2terrn/processing/terrain/elevation_service.py:83-140`; `osm2terrn/processing/terrain/heightmap_handler.py:44-67`; use mocked response first. |
| `P3-U006` | Runtime unresolved | Whether the menu can complete a selected city download and preserve state in a user session. | CLI/data-menu call path; test with injected renderer and provider mocks, no live network. |
| `P3-U007` | Runtime/output unresolved | Actual files and content produced by export, including heightmap dimensions and OTC/TERRN2 references. | `osm2terrn/processing/orchestrator.py:187-275`; controlled temporary output with synthetic inputs and mocked providers. |
| `P3-U008` | Static coverage limit | Notebook cells are excluded from current Python AST inventory. | `entry_points.jsonl` notebook uncertainty; analyze cells before drawing notebook paths. |
| `P3-U009` | Static coverage limit | Dynamic callbacks, environment-dependent configuration, cache state and exceptions can alter observed execution. | `osm2terrn/cli/menu.py`, `osm2terrn/config/`, `osm2terrn/cache/`, and provider boundaries; unresolved relations remain unresolved. |
| `P3-U010` | Historical test-status question; partially superseded by later recorded suites | The original source-reconstruction pass did not check outcomes. Later historical reports record 106 passed/1 skipped for a focused offline suite and 130 passed/1 skipped for a distinct expanded suite; their execution dates are absent. These results do not cover every test originally listed: `test_cli_config_overrides.py` and `test_download_menu.py` are not in either recorded command. The 130-test command does include `test_config_precedence.py`. No suite was executed for the 2026-11-09 documentation correction. | `tests/test_cli_config_overrides.py`, `tests/test_config_precedence.py`, `tests/test_download_menu.py`, `tests/test_osm_data_handler_cache.py`, `tests/test_osm_loader_cache.py`, `tests/test_road_export.py`, `tests/test_pipeline_domain_state.py`; historical commands/results in `verification_plan.md`. |
| `P3-F004` | Static configuration finding | `export.include_roads` is declared, parsed, and CLI-overridable, but no read was found in the inspected OSM acquisition/export path. | `P3-E026`; decide whether it gates query, conversion, output, or is obsolete; confirm with a focused mocked test after design approval. |
| `P3-F005` | Static boundary finding | The downloaded `roads` bundle value is a locally projected NetworkX graph; `roads_gdf` expects a GeoDataFrame and adapter-built domain map declares EPSG:4326. Directly wiring the current value to the current argument would not be a valid conversion. | `P3-E022`, `P3-E023`; design a typed graph/CRS/origin adapter before implementation. |
| `P3-F006` | Static state-flow finding | `dlcity()` returns on empty place/bbox without clearing prior `current_map` state; `export()` accepts any nonempty prior state. Cancel/manual selection after a successful earlier download can therefore leave stale data available to export. | `P3-E027`; maintainer must decide whether a cancelled/invalid new selection preserves or invalidates the previous session map; cover with stateful unit tests. |
| `P3-F007` | Static interface/documentation discrepancy | The lower-level road loader accepts a bbox and documents it as `(north, south, east, west)`, unlike the custom menu/downloader `(west, south, east, north)` tuple. The active road builder passes a place only. | `P3-E017`, `P3-E028`; do not wire the bbox argument into the road builder until tuple order and OSMnx API expectations are confirmed by unit/mock tests. |
| `P3-U011` | Design unresolved | Whether manually selected bbox may omit a place label, and how an unnamed area is named in session state, output files, TERRN2 metadata, and road lookup. | `../data-handoff-analysis.md`, Investigation A; maintainer decision followed by fake-renderer and temporary-output tests. |
| `P3-U012` | Design unresolved | Whether `preload_elevation` controls only eager acquisition, all terrain DEM acquisition, or road DEM sampling as well. | `../data-handoff-analysis.md`, Investigation B; explicit setting contract and mocked provider/cache tests. |
| `P3-U013` | Historical design proposal; implementation status updated 2026-10-20 | The canonical graph handoff, explicit acquisition result, output gate, and CRS conversions are implemented with focused synthetic coverage. The previous “pending approval” wording is superseded. Live-provider and full application behavior remain unverified. | `../execution/data-handoff-analysis.md`, “Implementation status”; `tests/test_street_network_handoff.py`. |
| `P3-U014` | CRS handling adjusted; real-source relationship unverified | The graph stays canonical; processing explicitly transforms edge geometries to origin-centered AEQD and the MapData view to EPSG:4326. Synthetic tests cover transforms. The AEQD definition now explicitly uses WGS84 ellipsoid after PROJ rejected the previous definition. Accuracy against real provider CRS metadata and terrain/elevation output remains unverified. | `osm2terrn/utils/geometry/crs.py::local_crs_from_lonlat`; `osm2terrn/adapters/coordinate_transform.py`; `../execution/data-handoff-analysis.md`. |

Do not convert an item to “verified” from a passing static inventory check. A
future test result must include the command/environment/revision and the
specific assertions it covers; a test may still leave unrelated branches open.

## Offline validation follow-up

The current mocked acquisition path distinguishes `not_requested`, successful
`empty`, `available`, and `failed` layer results. Successful empty geometry is
cacheable. Successful layers are also cached independently, so they survive a
different layer's failure; failed results are never cached as successful
layers. OSMnx 2.1.0-style `ResponseStatusCodeError` messages such as
`"Server responded: 502 Bad Gateway"` and `"Server responded: 401
Unauthorized"` are classified as temporary and permanent, respectively, in
mocked tests. The bbox downloader retries temporary errors at most three times
per layer and 120 seconds total, uses full-jitter exponential backoff capped at
30 seconds, and respects `Retry-After` within the remaining budget. The
primary and alternate Overpass endpoints are configurable. The current OSM
bbox algorithm version is `"5"`. Per-layer cache keys include a separate
layer-cache version and the bbox algorithm version; the existing complete
bundle cache remains readable. A legacy entry keyed with algorithm `"4"` and
format `"2"` remains on disk and is not reused. Live provider behavior,
including real endpoint availability and retry timing, remains unverified.

The procedural road writer now resolves its default output directory from
`ProgramConfig.paths.output_dir`; an explicit `output_dir` is forwarded by
`build_roads_from_place()`. Synthetic tests cover a configured directory from
another working directory and argument forwarding. Existing geographic
validation outputs were not moved or regenerated.

The scale characterization test measures a requested bbox at approximately
1062.69 × 1005.25 m, its first computed world size at 2048, the resulting
square bounds at approximately 2073.82 × 2048 m, and a second computed world
size at 4096 when that square envelope is independently recomputed. This
characterizes the former CLI/export double-rounding path. The user selected
an approximately 2048 m target. `MapData`
now retains the first computed size through CLI export, and a synthetic
integration test confirms that 2048 is passed for both OTC horizontal world
dimensions instead of recomputing 4096 from the geographic envelope. Runtime
interpretation of `WorldSize`, real DEM alignment, and street-DEM edge
behavior remain open; no elevation-sampling algorithm change was made.

## Street handoff follow-up — 2026-10-20

The following historical findings describe the pre-implementation route and
are addressed by the synthetic-tested graph handoff: `P3-F003` (bundle was
not transferred), `P3-F004` (`export.include_roads` had no consumer), and
`P3-F005` (graph/GDF type and CRS boundary was not adapted). `P3-F003` should
not be read as a current source description. `P3-F006` and `P3-F007` remain
outside scope. `P3-U004`, `P3-U007`, and `P3-U009` remain runtime/output limits.

The focused test command and covered assertions are recorded in
`data-handoff-analysis.md`. No live OSM query, terrain generation, interactive
application route, or simulator loading was performed. Static graph/GDF
validation and synthetic execution do not establish those behaviors.

## P1 integration test follow-up — 2026-10-20

`tests/test_street_network_integration.py` now exercises the real
`dlcity()` → `export()` → `export_terrain_assets()` code path with the menu,
provider, elevation fetch and writers mocked. It narrows `P3-U006` (CLI
reachability) for the mocked path only and `P3-U014` for synthetic CRS
transforms. Real-provider payloads, real elevation, cross-process cache and
Rigs of Rods loading remain unverified.

| ID | Type | Statement | Evidence / next step |
|---|---|---|---|
| `P3-U015` | Resolved 2026-10-27 (synthetic tests) | Policy: acquisition status reports only graph acquisition/recovery. A graph→MapData conversion failure sets `road_mapdata_status=failed` and `road_mapdata_diagnostic` (exception type only), keeps `road_acquisition_status=available`, marks `road_processing_status`/`road_export_status=failed`, `roads_exported=False`, and `_export_roads` does not call `build_roads_from_graph`. Heightmap, groundmap and OTC/terrn2 stages continue. An invalid/non-`StreetNetworkResult` entry remains an acquisition `failed`. In the mocked CLI test, `commands.export()` still returns `None` (no consumer uses it); `export_terrain_assets()` now also returns `roads_outcome` (`failed` when export failed or acquisition failed, otherwise the export status or `disabled`) and the CLI prints a "Partial export ... roads were NOT exported" message plus a warning log instead of "Export complete". Valid `empty`, `skipped` and `disabled` roads still print "Export complete". A failing mandatory terrain stage still raises into the CLI's "Error during export" path. No interactive terminal session or process exit code was tested. | `osm2terrn/processing/orchestrator.py` (`export_terrain_assets`, `_export_roads`); `test_cli_mapdata_conversion_failure_fails_roads_globally_but_keeps_terrain_stages`, `test_invalid_street_result_is_acquisition_failure_distinct_from_conversion_failure`. |
| `P3-U016` | Resolved 2026-10-27 (synthetic tests) | Contract: `empty` may carry a nodes-only graph plus matching `graph_crs` (both or neither; zero edges; explicit CRS). `graph=None` means no nodes at all. `available` still requires edges; other statuses still forbid a graph. Acquisition keeps the transformed nodes-only graph; a nodes-only graph without CRS is `failed`. Consumers act only on `available`, so none uses the graph of `empty`. `_OSM_BBOX_ALGORITHM_VERSION` raised `"2"`→`"3"`; a version-2 entry was not reused by `download_data_from_bbox()` using version 3. A separate two-process `FileCacheBackend` test restored empty, nodes-only, and available `StreetNetworkResult` instances including graph data. Not verified: real OSM provider payloads or a disk-cache round trip containing real provider data. | `osm2terrn/data/street_network.py`; `osm_data_handler.py`; tests `test_valid_empty_provider_graph_is_empty_not_failed`, `test_provider_graph_without_nodes_is_completely_empty`, `test_nodes_only_graph_without_crs_is_failed_not_empty`, `test_street_result_contract_for_empty_with_graph`, `test_nodes_only_empty_result_round_trips_through_cache_and_skips_roads`, `test_cli_empty_street_result_is_reported_as_empty_not_failed`, `tests/test_street_cache_process.py`. |
| `P3-U017` | Resolved 2026-10-27 | The two duplicated tests were identical (diff: 0 differences); the hidden copies and one repeated assertion block were removed with no assertion lost. All 12 `test_` names in `tests/test_street_network_handoff.py` are now unique. | `tests/test_street_network_handoff.py`. |
| `P3-U018` | Resolved 2026-10-28 (synthetic tests); exit code and real providers open | `road_network is None` is not a valid acquisition outcome: `download_data_from_bbox` always stores a `StreetNetworkResult`. `None` occurs only if `current_map.data` loses `roads` or `export_terrain_assets()` is called directly. With `include_roads=True`, `None`/`missing` now gives `roads_outcome=failed` and `not_requested` gives `roads_outcome=not_requested`; the CLI prints "Partial export" with a reason plus a warning. `empty`/nodes-only, `available` and `disabled` still print "Export complete". `missing` is not produced by any acquisition path found. Still open: whether `not_requested` with `include_roads=True` should instead be a configuration error, and the process exit code (unchanged). | `osm2terrn/processing/orchestrator.py` (`_roads_outcome`); `osm2terrn/cli/commands.py` (`export`); `test_cli_lost_street_result_is_partial_export_not_success`, `test_cli_roads_not_requested_by_network_config_is_reported_not_complete`, `test_cli_roads_disabled_with_lost_result_is_still_complete`. |
