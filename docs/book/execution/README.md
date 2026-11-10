# Execution Map — Stage 3

## Scope and evidence rules

This folder reconstructs the declared application startup and the code paths
that can be followed from it. It is a source-based map, not a record of an
application run. No terrain generation, geographic download, application test,
or network request was performed while preparing it.

Use these labels throughout:

- **Code fact**: explicit declaration or direct call/branch in the cited file.
- **Static inference**: consequence of connected code statements, not observed
  at runtime.
- **Candidate**: a declared/detected invocation surface whose usability or
  support has not been executed and verified.
- **Unresolved**: current source or available artifacts do not settle it.
- **Runtime observed**: reserved for a future run with command, environment,
  repository revision, result, and retained output that another reviewer can
  inspect. Inventory metadata alone is not sufficient.

## Entry-point map

The 2026-10-20 inventory snapshot listed 41 entry records. The refreshed
2026-11-07 inventory lists 47. They include the application,
tests, documentation tooling, scripts, a notebook, and pytest discovery
surfaces. The generator marks all of them `support_status=unconfirmed`; that
label is detection status, not an independent finding that each is supported.

| Surface | Evidence in source | Assessment |
|---|---|---|
| Installed `osm2terrn` console command | `pyproject.toml` declares `osm2terrn = "osm2terrn.app.main:main"` at lines 105–106. | **Declared application candidate.** Installation/command execution was not tested. |
| `python -m osm2terrn` | `osm2terrn/__main__.py` imports `main` and raises `SystemExit(main())` at lines 1–3. | **Implementation-backed application candidate.** No runtime claim. |
| Windows `start.bat` | Invokes `.venv\Scripts\python.exe osm2terrn\__main__.py` then pauses (lines 1–2). | **Launcher candidate.** Depends on a local `.venv` and Windows; not tested. |
| `python osm2terrn/app/main.py` | `app/main.py` has a main guard at lines 184–185. | **Candidate; support unresolved.** The package import path and direct-script behavior were not executed. |
| Former root README `python main.py` instruction | No root `main.py` exists in the current tree; README was corrected on 2026-11-07 to use `python -m osm2terrn`. | **Historical documentation defect corrected.** Package installation/command execution is still not verified here. |
| Test entry points / pytest modules | `entry_points.jsonl` records `tests/run_bbox_tests.py`, selected `test_*.py`, and `tests/conftest.py`. | **Test surfaces, not application launchers.** Their presence does not mean they passed. |
| Scripts | Inventory detects `scripts/smoke_export_luis_guillon.py`, `scripts/terrain_colors_demo.py`, and `scripts/testing_layout_generator.py`. | **Tools/candidates.** Their runtime support and side effects are not established here. The smoke script was not run. |
| Notebook | Inventory lists `notebooks/osm2tern_notebook.ipynb` and says cells were not analyzed. | **Unresolved interactive surface.** No notebook-cell call graph is available. |
| Inventory generator | Its own main guard is inventoried. | **Documentation tooling, not an OSM2Terrn application entry point.** |

The latest generated report records 347 file records, 147 parsed Python files,
1,007 symbols, 2,505 relations, 2,317 unresolved items, and 47 entry points.
These are static snapshot counts, not proof of complete coverage.

## Main application startup

The main route supported by declarations and source is:

1. The installed console script dispatches to `osm2terrn.app.main:main`, or
   `python -m osm2terrn` executes `osm2terrn/__main__.py` and calls the same
   function.
2. Importing `osm2terrn.app.main` calls `load_dotenv()`; it also imports the
   configuration facade. `main()` builds an `argparse` parser and parses
   `argv` or process arguments.
3. It selects `project_dir` from `--project-dir` or
   `OSM2TERRN_PROJECT_DIR`; it builds program and project override mappings.
   Conflicting boolean flags and a lone terrain output width/height are
   rejected through `parser.error`.
4. `ProjectLoader` loads typed program configuration and project
   configuration. The project loader starts from defaults, optionally reads a
   selected project file and its `include`/`includes`, then applies legacy,
   CLI, and interface overrides. A missing include or circular include raises
   `ValueError`; an absent explicit config path currently resolves to no file
   rather than being reported here as a startup error.
5. `configure()` stores both configuration objects. Only after that does
   `main()` import `osm2terrn.cli.menu`; that module imports the command
   functions, whose module-level `_PROJECT_CONFIG = get_project_config()` is
   therefore initialized after the explicit configuration in this route.
6. `mainmenu.run()` loops over interactive actions. `run_once()` renders the
   menu, reads a key, executes the selected callback, catches ordinary
   `Exception` from that callback, and returns. `SystemExit` from the exit
   action is not an `Exception` and propagates.

The parser declares project/config, output/log/cache path overrides, terrain
size/colormap/smoothing, road type/simplification/widths, buildings enabled,
ground texture, output name, road/building export toggles, and elevation
preload toggles. The exact flag declarations and mutual-exclusion rules are in
`osm2terrn/app/main.py:20-154`.

## Current code-level findings

These are source-derived findings, not runtime observations:

1. **Manual bounding-box route returns to the main menu.**
   `DownloadMenu.show_main_menu()` returns `("", bbox)` for a custom box
   (`osm2terrn/data/download_menu.py:48-49`). `dlcity()` immediately returns
   when either `place` or `bbox` is false (`osm2terrn/cli/commands.py:27-30`).
   Thus the current manual-box result is rejected before
   `download_data_from_bbox()` is called. This early return does not clear
   prior `current_map` data, which can remain available to the later export
   guard. These are static control/state-flow consequences; no UI interaction
   was performed. See [`data-handoff-analysis.md`](data-handoff-analysis.md).
2. **The elevation prefetch flag is not consulted by `dlcity()`.** The parser
   maps `--pipeline-preload-elevation` to project config, and the config model
   contains `preload_elevation`, but `dlcity()` calls `heightmapper(...)`
   unconditionally after storing map state (`osm2terrn/cli/commands.py:65-79`).
   Searches of the application source found no use of this project field in
   the download action. The default/override is therefore not shown to control
   that prefetch path.
3. **Street graph handoff — current source path, static finding.** Earlier
   Stage 3 records below describe the pre-change gap: the CLI omitted the
   downloaded bundle from export. The current callback passes stored
   `StreetNetworkResult` to `export_terrain_assets()`; the orchestrator uses
   an explicit graph-aware adapter and graph-based road processing. See
   `osm2terrn/cli/commands.py:90-115`,
   `osm2terrn/processing/orchestrator.py`, and the dated implementation record
   in `data-handoff-analysis.md`. Synthetic tests cover selected conversions
   and states. Real-provider and complete interactive behavior remain
   unverified.

The manual bbox guard and unused elevation-preload setting are source findings,
not fixes made in this documentation task. The street handoff is implemented
in application code and its status is documented; no application code was
changed during this documentation consolidation.

## Reading order

- [`call_paths.md`](call_paths.md) — startup, download, state and export routes.
- [`module_map.md`](module_map.md) — responsibilities and data boundaries.
- [`evidence_register.md`](evidence_register.md) — source locators and certainty.
- [`uncertainties.md`](uncertainties.md) — open questions and code findings.
- [`verification_plan.md`](verification_plan.md) — safe follow-up checks.
- [`data-handoff-analysis.md`](data-handoff-analysis.md) — Stage 3.2 deep
  analysis of bbox identity, elevation setting, street data transfer, design
  choices, and a mock-based test plan.
- [`diagrams/application-flow.mmd`](diagrams/application-flow.mmd) — Mermaid flow.
