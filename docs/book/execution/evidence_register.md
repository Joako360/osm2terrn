# Evidence Register — Stage 3

Evidence IDs below are stable within this document set. All evidence is
source/static. No runtime observation is recorded.

| Evidence ID | Claim supported | Source and locator | Type / certainty |
|---|---|---|---|
| `P3-E001` | Installed script maps `osm2terrn` to `osm2terrn.app.main:main`. | `pyproject.toml:105-106` | Configuration fact; runtime install untested. |
| `P3-E002` | Module launcher calls the same `main()` and exits with its return code. | `osm2terrn/__main__.py:1-3` | Direct source fact. |
| `P3-E003` | Windows launcher selects a `.venv` interpreter and pauses afterward. | `start.bat:1-2` | Direct source fact; launcher untested. |
| `P3-E004` | Root README advertises `python main.py`, but no root `main.py` exists in this tree. | `README.md:78-85`; repository path inventory | Direct file-presence finding. |
| `P3-E005` | Startup parses CLI, resolves project dir/env, loads two configs, configures settings, imports menu, and runs it. | `osm2terrn/app/main.py:156-185` | Direct source sequence; not observed execution. |
| `P3-E006` | Project config precedence includes defaults, project files/includes, CLI, interface. | `osm2terrn/config/loader.py:58-97,122-160,174-184` | Direct source fact. |
| `P3-E007` | Menu dispatch callbacks include download, load/import, export, exit. | `osm2terrn/cli/menu.py:118-155,68-115` | Direct source fact. |
| `P3-E008` | Manual bbox result uses empty place; `dlcity` rejects falsy place before bbox download. | `osm2terrn/data/download_menu.py:48-49`; `osm2terrn/cli/commands.py:21-35` | Static control-flow inference from direct return/predicate. |
| `P3-E009` | OSM bbox handler checks cache, calls configured feature/network providers, transforms, catches per-entry errors and caches bundle. | `osm2terrn/data/osm_data_handler.py:56-169` | Direct source fact; network path not run. |
| `P3-E010` | `dlcity` preloads elevation unconditionally; config flag is mapped but not consulted by this action. | `osm2terrn/cli/commands.py:65-79`; `osm2terrn/app/main.py:56,142-150`; `osm2terrn/config/models.py:201,272-273` | Static comparison; behavior in another unseen caller not claimed. |
| `P3-E011` | Export constructs `MapData` without a roads GeoDataFrame; adapter yields empty roads when `roads_gdf` is absent. | `osm2terrn/processing/orchestrator.py:187-205`; `osm2terrn/domain/adapters/osmnx_to_map.py:54-105` | Direct source plus static inference. |
| `P3-E012` | Road exporter skips empty domain roads; otherwise it loads graph by place. | `osm2terrn/processing/orchestrator.py:151-185`; `osm2terrn/processing/network/road_network_export.py:40-60` | Direct source fact. |
| `P3-E013` | Heightmap path can use passed elevation or fetch; fetch exceptions fall back to a flat raster. | `osm2terrn/processing/terrain/heightmap_handler.py:44-67` | Direct source fact; branch execution unknown. |
| `P3-E014` | Export writes image outputs, optional roads, OTC files, manifest TOBJ and TERRN2. | `osm2terrn/processing/orchestrator.py:187-275` | Direct call sequence; writes not run. |
| `P3-E015` | Inventory records 41 entry points with unconfirmed support; notebook cells not analyzed. | `docs/book/inventory/entry_points.jsonl`; `docs/book/progress/inventory_report.md:16-19` | Static artifact fact. |
| `P3-E016` | `load()` is a placeholder and does not load map data. | `osm2terrn/cli/commands.py:82-87` | Direct source fact. |
| `P3-E017` | Manual bounds are `(west, south, east, north)` and range/order checked; the option returns the valid tuple with an empty label. | `osm2terrn/data/download_menu.py:48-78`; `osm2terrn/data/download_menu_components.py:27-37` | Direct source fact. |
| `P3-E018` | The bbox downloader accepts coordinates without a place label; the CLI guard requires both label and bbox before calling it. | `osm2terrn/data/osm_data_handler.py:56-68`; `osm2terrn/cli/commands.py:27-35` | Static control-flow inference; supports that the guard is the blocker, not that product intent permits anonymous areas. |
| `P3-E019` | Session `MapData` and domain `MapData` are distinct classes; only the first stores raw bundle and session metadata. | `osm2terrn/app/app_state.py:6-21`; `osm2terrn/domain/entities/map_data.py:18-32` | Direct source fact. |
| `P3-E020` | `preload_elevation` defaults true, is parsed and can be CLI-overridden; the current `dlcity()` call path does not read it. | `osm2terrn/config/models.py:197-202,264-275`; `osm2terrn/config/defaults.py:97-103`; `osm2terrn/app/main.py:56-57,142-150`; `osm2terrn/cli/commands.py:70-79` | Direct source facts plus scoped source-search result; no claim about external library internals. |
| `P3-E021` | Export uses valid supplied elevation or falls back to a provider function; provider cache may avoid a network transfer; a separate road DEM sampler exists. | `osm2terrn/processing/terrain/heightmap_handler.py:44-67`; `osm2terrn/processing/terrain/elevation_service.py:83-131`; `osm2terrn/processing/roads/road_elevation.py:13-32` | Static call/data-flow facts; cache and provider outcomes unknown. |
| `P3-E022` | Default OSM config has a `roads` network key; download bundle entries are transformed NetworkX graphs or `None`; configured network keys are iterated. | `osm2terrn/config/defaults.py:60-88`; `osm2terrn/data/osm_data_handler.py:21-24,132-167`; `osm2terrn/adapters/coordinate_transform.py:76-112` | Direct source fact; actual configured key and response unknown. |
| `P3-E023` | Export omits `roads_gdf`; adapter maps omitted value to `roads=[]`, while a supplied GeoDataFrame is converted to domain roads. | `osm2terrn/processing/orchestrator.py:187-205`; `osm2terrn/domain/adapters/osmnx_to_map.py:54-119`; `osm2terrn/domain/adapters/osmnx_to_roads.py:45-99` | Static data-flow inference; adapter cache state was not inspected at runtime. |
| `P3-E024` | Empty domain roads return before place-based road loading; if reached with roads, builder performs a separate place query and writes a roads TOBJ. | `osm2terrn/processing/orchestrator.py:151-184`; `osm2terrn/processing/network/road_network_export.py:40-65,94-196`; `osm2terrn/data/osm_loader.py:17-65` | Static call-flow fact; current UI route's empty adapter input makes the reload branch not reached on the inspected path. |
| `P3-E025` | Roads TOBJ is included in TERRN2 objects only when a path exists; the domain manifest is built from domain feature lists. | `osm2terrn/processing/orchestrator.py:57-123,252-281`; `osm2terrn/processing/terrain/terrn2_entrypoint.py:102-123` | Direct source fact; no output files inspected. |
| `P3-E026` | `export.include_roads` has defaults and CLI/config parsing, but no application consumer was found in the inspected export/acquisition path. | `osm2terrn/app/main.py:50-54,123-137`; `osm2terrn/config/models.py:188-194,264-270`; `osm2terrn/config/loader.py:348-352` | Scoped negative source-search result; intent unresolved. |
| `P3-E027` | The no-place/no-bbox early return in `dlcity()` leaves existing session state untouched; export later checks only whether session data is nonempty. | `osm2terrn/cli/commands.py:27-30,36-40,96-99`; `osm2terrn/app/app_state.py:11-18` | Static state-flow inference; whether preserving prior selection is intended is unresolved. |
| `P3-E028` | `load_graph()` accepts `place` or `bbox` and documents bbox order as `(north, south, east, west)`; `build_roads_from_place()` supplies only `place`. | `osm2terrn/data/osm_loader.py:17-39,61-65`; `osm2terrn/processing/network/road_network_export.py:40-54` | Direct source fact; bbox order/provider compatibility not tested. |
| `P3-E029` | The selected Nominatim result returns a place label derived from the first component of `display_name`; the menu return does not include its OSM ID/type. | `osm2terrn/data/download_menu_components.py:15-21,35-37`; `osm2terrn/data/download_menu.py:42-49` | Direct source fact; whether this label identifies the same extent on a later place query is unresolved. |

## Current source follow-up — 2026-11-07

The rows above are retained as historical locators from earlier inspections.
The following current-tree observations were rechecked for this consolidation;
locators identify files/symbols rather than line offsets because offsets may
move. See the generated inventory for current line ranges. None is a runtime
observation.

| Evidence ID | Claim supported | Source and locator | Type / certainty |
|---|---|---|---|
| `P3-E030` | Package metadata requires Python 3.12+, declares dependencies and maps the `osm2terrn` console command to `osm2terrn.app.main:main`. | `pyproject.toml`: `[project]`, `dependencies`, `[project.scripts]` | Direct metadata fact; installation/execution untested in this task. |
| `P3-E031` | `python -m osm2terrn` delegates to application `main()`. | `osm2terrn/__main__.py` | Direct source fact; not executed in this task. |
| `P3-E032` | Current CLI export passes stored road acquisition state to the orchestrator, which uses the graph-aware adapter/road processing path. | `osm2terrn/cli/commands.py`: `export`; `osm2terrn/processing/orchestrator.py`: `export_terrain_assets`; `osm2terrn/domain/adapters/` | Static call/data-flow finding; synthetic evidence is separately reported; no live route verified here. |
| `P3-E033` | Current layer and street result models expose explicit acquisition statuses, including successful empty and failure states. | `osm2terrn/data/acquisition.py`; `osm2terrn/data/street_network.py` | Direct source fact; does not prove provider outcomes. |
| `P3-E034` | Current geographic validation reports record bounded runs and do not establish successful simulator loading; the second report records OSM layer failures for that run. | `docs/book/validation/first_geographic_validation.md`; `second_geographic_validation.md` | Historical execution evidence as reported by those documents; not rerun during this documentation task. |

The source-based street handoff update supersedes the pre-change claims in
`P3-E011`/`P3-E023`/`P3-E026` for the current implementation. Their historical
wording remains to preserve review history. The corresponding status is
qualified in `uncertainties.md` and `data-handoff-analysis.md`.

## Reading rule

An evidence row establishes only the cited declaration/call/condition. It does
not establish reachability, successful imports, external-service responses,
output files, or a passed test. The inventory currently marks generated
records `execution_status=not_verified`; this register does not add execution
evidence.
