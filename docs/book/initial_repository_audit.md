# Initial Repository Audit

## Scope and method

This is a static inspection of the repository filesystem and the current Git
working tree. It records observable structure and source/documentation
evidence; it does not describe a proposed architecture as though it were
implemented.

- No application code, tests, or external services were executed.
- No network requests or downloads were made.
- `.env` was not opened. Only the existence of the file and the variable names
  in `.env.example` were observed; no secret values are reproduced here.
- The requested destination, `docs/book/initial_repository_audit.md`, did not
  exist when checked.
- The working tree was already dirty: 19 tracked paths were modified and one
  untracked file existed at inspection time. Findings describe the present
  filesystem, not a clean checkout or an attribution of those changes.
- The root contains 234 Git-tracked files, including 94 Python files under
  `osm2terrn/`, 28 paths under `tests/`, and 62 tracked documentation files
  under `docs/`. One additional, untracked architecture document is present.
- Local ignored directories were identified by name and approximate size; their
  contents were not incorporated into the source inventory.

## Repository status summary

The project is a Python package for generating Rigs of Rods terrain assets from
geospatial data. The source package has distinct `app`, `cli`, `config`,
`data`, `domain`, `processing`, `tools`, and `utils` areas, alongside two
adapter locations. Configuration examples are under `projects/template/`.
There is a substantial, topic-oriented documentation set and a pytest test
suite.

The current checkout has ongoing local changes. The modified paths include
`.vscode/settings.json`, production modules across `osm2terrn/`, and tests;
`docs/architecture/PHASE-1-COMPLETION.md` is untracked. Any statements about
current code should therefore be read as a snapshot, not as a comparison
against an unmodified release.

An important structural inconsistency is that code and tests import modules
from `osm2terrn.cache`, while no `osm2terrn/cache/` package or files were
present in the inspected filesystem or tracked-file list. A root-level
`cache/` directory does exist, but it is ignored runtime data, not that Python
package. This is a source-level observation, not an executed import failure.

## Relevant structure

```text
.
├── .github/
│   ├── instructions/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── projects/
├── docs/
│   ├── architecture/          # architecture guides and ADRs
│   ├── cli-flow/              # CLI workflow notes
│   ├── elevation-realism/
│   ├── exporters/
│   ├── function-reference/
│   ├── opentopography-api/
│   ├── testing-validation/
│   └── troubleshooting/
├── notebooks/
├── osm2terrn/
│   ├── adapters/               # coordinate transforms
│   ├── app/                    # app entrypoint and in-memory map state
│   ├── cli/                    # menu and commands
│   ├── config/                 # config models, loading, defaults and paths
│   ├── data/                   # OSM and other provider acquisition
│   ├── domain/
│   │   ├── adapters/
│   │   ├── entities/
│   │   └── value_objects/
│   ├── processing/
│   │   ├── network/
│   │   ├── otc/
│   │   ├── roads/
│   │   └── terrain/
│   ├── tools/visualization/
│   └── utils/
│       ├── geometry/
│       ├── hashing/
│       └── io/
├── projects/template/          # YAML project configuration
├── scripts/                    # examples and helper programs
├── tests/                      # pytest tests and a standalone bbox runner
├── pyproject.toml
├── uv.lock
├── README.md
├── ROADMAP.md
└── TODO.md
```

Other tracked root documents include `CONTRIBUTING.md`, `SECURITY.md`,
`CODE_OF_CONDUCT.md`, `PROJECT_UPDATE_SUMMARY.md`, `LICENCE.txt`, and
`description.txt`. `start.bat` is a Windows launcher. No root `src/`
directory, root `main.py`, or `requirements.txt` was present.

The source includes models such as `BoundingBox`, `Point2D`, `Point3D`,
`Polyline`, `Polygon`, `Road`, `Building`, `Railway`, `WaterBody`, and map
entities. Their implementations are distributed across
`osm2terrn/domain/entities/` and `osm2terrn/domain/value_objects/`; the
`domain` package is not the only place containing data structures (for
example, `osm2terrn/app/app_state.py` holds mutable session state).

## Entry points and execution paths

### Application entry points

1. **Module execution:** `python -m osm2terrn` resolves to
   `osm2terrn/__main__.py`, which imports and exits through
   `osm2terrn.app.main:main`.
2. **Installed console command:** `pyproject.toml` declares the `osm2terrn`
   script as `osm2terrn.app.main:main`.
3. **Windows launcher:** `start.bat` invokes
   `.venv\Scripts\python.exe osm2terrn\__main__.py` and then pauses.
4. **Application function:** `main(argv=None)` in
   `osm2terrn/app/main.py` parses CLI flags, loads program/project
   configuration, applies overrides, configures the application, and starts
   `mainmenu.run()` from `osm2terrn/cli/menu.py`.

The CLI is an interactive menu rather than a set of declared argparse
subcommands. Its primary branches are:

- **Download:** the menu in `osm2terrn/data/download_menu.py` offers place-name
  search, a manually entered bounding box, or cancellation. Place search uses
  OSMnx's Nominatim request helper; manual input validates coordinate ranges.
  `osm2terrn/cli/commands.py::dlcity` downloads data, stores map/session
  information in `current_map`, and attempts elevation prefetch.
- **Load/import:** `osm2terrn/cli/commands.py::load` currently displays a
  “coming soon” message; it does not implement the cached-data loading
  described by some user-facing documentation.
- **Export:** `osm2terrn/cli/commands.py::export` requires current map data and
  calls `export_terrain_assets` in `osm2terrn/processing/orchestrator.py`.
  That orchestration builds a domain map, writes heightmap/groundmap assets,
  attempts optional road output, emits paged and global OTC files, writes a
  TOBJ manifest, and creates the TERRN2 entrypoint.
- **Quit:** the menu exit action terminates the process.

### Other executable or test-oriented files

- `scripts/smoke_export_luis_guillon.py` has a `main()` guard and selects
  smoke/full exporter behavior.
- `scripts/testing_layout_generator.py` has a `main()` guard for interactive
  procedural layout generation.
- `scripts/terrain_colors_demo.py` has a direct-execution guard.
- `scripts/pseudo_layout_generator.py` contains a procedural transport-network
  class and plotting code.
- `scripts/fix_processing_imports.py` is a helper script; its presence does not
  establish a supported application entry point.
- `tests/run_bbox_tests.py`, `tests/test_offset_fix.py`, and
  `tests/test_road_export.py` contain direct-execution guards. The remaining
  `tests/test_*.py` files are pytest-style tests.
- `notebooks/osm2tern_notebook.ipynb` is a notebook-based exploration surface.

The helper scripts may have side effects or require data and services; none
were run during this inspection.

## Technologies and dependencies

### Python and packaging

- **Declared Python requirement:** `>=3.12` in `pyproject.toml`.
- **Build backend:** setuptools (`setuptools>=80`) with `wheel`.
- **Project version:** `0.1.0`.
- **Console script:** `osm2terrn = osm2terrn.app.main:main`.
- **Lock file:** `uv.lock` is present. `pyproject.toml` is the direct dependency
  declaration.
- **No `requirements.txt` was found**, despite installation instructions that
  refer to it.

### Direct runtime dependencies

`pyproject.toml` declares:

- GIS and spatial: `geopandas`, `pyproj`, `rasterio`, `shapely`, `osmnx`,
  `fused`
- Numeric and raster/color processing: `numpy`, `scipy`, `matplotlib`,
  `Pillow`, `cmasher`, `cmcrameri`, `colorcet`
- Graph processing: `networkx`
- HTTP/config/CLI: `requests`, `python-dotenv`, `rich`

Build dependencies are `setuptools` and `wheel`. Optional groups declare:

- `dev`: `autopep8`, `black`, `deptry`, `ipykernel`, `pip-review`, `ruff`,
  `spyder-kernels`
- `test`: `pytest`, `pytest-cov`
- `docs`: `myst-parser`, `numpydoc`, `sphinx`

No `mypy` dependency or explicit Ruff/Black configuration was found in
`pyproject.toml`. No separate tracked `tox.ini`, `pytest.ini`, `setup.cfg`,
`noxfile.py`, or Sphinx `conf.py` was found in the inspected root/docs layout.

### External data sources and API-related configuration

These are source-level integrations; no requests were made.

- **OpenStreetMap:** OSMnx calls in `osm2terrn/data/osm_data_handler.py` and
  `osm2terrn/data/osm_loader.py` obtain features and road graphs. OSMnx also
  backs place lookup in `osm2terrn/data/download_menu.py`, via Nominatim.
  OSMnx configuration includes Overpass-related settings.
- **Elevation:** `osm2terrn/processing/terrain/elevation_service.py` uses
  `requests` to call OpenTopography's GlobalDEM endpoint and sends the API key
  under the `API_Key` query parameter. The key is read by the configurable
  environment-variable name whose default is
  `OPENTOPO_ELEVATION_API_KEY`.
- **OpenTopoData:** `ProviderConfig` in `osm2terrn/config/models.py` declares
  an OpenTopoData elevation URL template, and `osm_data_handler.py` assigns
  that configured template to OSMnx. This is distinct from the explicit
  OpenTopography GlobalDEM request in `elevation_service.py`.
- **Overture Maps:** `download_builings_from_overture` in
  `osm2terrn/data/osm_data_handler.py` loads and runs a Fused UDF referenced by
  URL. The code contains a separate building-data acquisition path.

Variable names found in `.env.example` include
`OPENTOPO_ELEVATION_API_KEY`, `OVERPASS_MAX_QUERY_AREA_SIZE`,
`OVERPASS_REQUESTS_TIMEOUT`, `OVERPASS_RATE_LIMIT`, and `OVERPASS_URL`.
Additional application environment names are used for project selection,
logging, and current place/origin metadata. Their values are intentionally
omitted.

## Observable architecture and conventions

### Facts observed in code

- The package is organized into acquisition (`data`), app/CLI, configuration,
  domain entities/adapters, processing, and shared utility packages.
- Processing is subdivided into terrain, roads, network, and OTC modules, with
  `osm2terrn/processing/orchestrator.py` coordinating the export path.
- GeoPandas/OSMnx data is adapted into project domain entities by modules such
  as `osm2terrn/domain/adapters/osmnx_to_roads.py` and
  `osm2terrn/domain/adapters/osmnx_to_map.py`.
- Spatial utilities and coordinate conversions are distributed between
  `osm2terrn/adapters/coordinate_transform.py`,
  `osm2terrn/utils/geometry/`, and `osm2terrn/domain/adapters/`.
- Configuration is represented by typed dataclasses in
  `osm2terrn/config/models.py`, loaded by `osm2terrn/config/loader.py`, and
  accessed through `osm2terrn/config/settings.py`. Project examples are
  separated into YAML files under `projects/template/`.
- The application has mutable module-level state (`current_map` in
  `osm2terrn/app/app_state.py`) and module-level configuration accessors/caches
  in `osm2terrn/config/settings.py`.
- Logging helpers live in `osm2terrn/utils/logger.py`; the CLI also writes
  user-facing messages through Rich.
- Cache operations are referenced throughout source, but their expected
  `osm2terrn/cache/` implementation was absent from the inspected tree.

### Inferences, not architectural guarantees

- The directory boundaries suggest an intended acquire/adapt/process/export
  flow, but actual dependencies cross those boundaries: processing and
  adapters directly import configuration and cache facilities, and
  application/CLI modules share global state.
- The ADRs express target decisions (including statelessness and adapter
  boundaries); they should be treated as design intent until each decision is
  verified against call paths and runtime behavior.
- A complete call graph and all conditional/fallback behavior require a
  follow-on source inventory; this initial audit only traced the main CLI and
  export route.

## Existing documentation

Useful starting points include:

- `README.md`: overview, installation, quick-start, project YAML, CLI flags,
  status, and high-level architecture.
- `CONTRIBUTING.md`: contribution, style, test, and logging guidance.
- `docs/README.md`: index to contributor documentation.
- `docs/architecture/`: architecture index, pipeline, module organization,
  data contracts, change map, and ADR-0001 through ADR-0009.
- `docs/cli-flow/`: download/export paths and behavior notes.
- `docs/function-reference/`: data, processing, utilities, and entrypoint
  references.
- `docs/exporters/` and `docs/exporters-docs.md`: exporter guidance.
- `docs/testing-validation/`: test baseline, functional workflow, matrix, and
  PR evidence.
- `docs/troubleshooting/`, `docs/opentopography-api/`, and
  `docs/elevation-realism/`: operational/provider-specific guidance.
- Root `ROADMAP.md` and `TODO.md`: planned work and task tracking.
- `.github/instructions/`: contributor instructions, including
  `docs.instructions.md`, `testing.instructions.md`, and
  `pipeline.instructions.md`.

## Documentation and organization discrepancies

The following are mismatches between inspected documentation and current
filesystem/source, not proposed fixes:

1. **Python floor differs.** `pyproject.toml` requires Python `>=3.12`, while
   `README.md` and `CONTRIBUTING.md` state Python 3.10+.
2. **Installation command references a missing file.** `README.md` tells users
   to install with `pip install -r requirements.txt`, but no
   `requirements.txt` exists. The project has `pyproject.toml` and `uv.lock`.
3. **Quick-start points to a missing root script.** `README.md` says
   `python main.py`; there is no root `main.py`. The package module and
   console-script entries are declared elsewhere in the README and project
   metadata.
4. **Architecture/function reference paths are stale.** For example,
   `docs/architecture/architecture-pipeline.md` names
   `osm2terrn/main.py`, `osm2terrn/utils/bbox.py`, and
   `osm2terrn/processing/heightmap_handler.py`; current corresponding paths
   include `osm2terrn/app/main.py`, `osm2terrn/utils/geometry/bounds.py`, and
   `osm2terrn/processing/terrain/heightmap_handler.py`.
   `docs/function-reference/function-reference-entrypoint.md` similarly
   locates `MapData` and CLI functions in `osm2terrn/main.py`, whereas they are
   separated into `app/app_state.py`, `cli/commands.py`, and `cli/menu.py`.
5. **Documented load behavior is ahead of implementation.** The README's
   interactive-menu description says “Load cached data”; the current
   `load()` in `osm2terrn/cli/commands.py` is a placeholder that prints a
   “coming soon” message.
6. **Testing baseline references a missing source directory.**
   `docs/testing-validation/testing-baseline.md` recommends
   `python -m compileall src`, but no top-level `src/` directory exists. The
   package is rooted at `osm2terrn/`.
7. **License filename differs from metadata.** `pyproject.toml` references
   `LICENSE`, while the tracked root license is `LICENCE.txt`.
8. **Cache architecture documentation conflicts with the filesystem.** The
   untracked `docs/architecture/PHASE-1-COMPLETION.md` says the cache
   infrastructure is centralized and depicts `osm2terrn/cache/`; no such
   source package was present. It also claims relevant tests pass; no tests
   were run for this audit, so that claim is not independently verified here.
9. **Provider naming can mislead.** Configuration and comments include an
   OpenTopoData URL template, while the explicit elevation downloader calls
   OpenTopography GlobalDEM. The exact user-facing provider path depends on
   which code path is active.
10. **CI automation was not found.** `.github/` contains instructions,
    templates, repository metadata, and a project-board file, but no
    `.github/workflows/` directory was present.

The documentation is mostly English, with parallel English/Spanish pages for
some guides. Some source comments/docstrings are also Spanish. The code and
documentation therefore do not have a single consistently enforced language
in practice, despite the project-level English-only instruction.

## Generated, local, sensitive, or bulky items to exclude from an ordinary
## document inventory

Observed local-only or ignored paths include:

- `.venv/`: approximately 12,735 files and 654.5 MB; environment/dependencies.
- `.examples/`: approximately 2,415 files and 484 MB; ignored sample/output
  content.
- `.docs/`: approximately 8.7 MB; ignored local documentation-related content.
- `.cache/` and root `cache/`: ignored cache data.
- `output/`: ignored generated output (approximately 7 files, 0.76 MB at
  inspection time).
- `logs/`: ignored runtime logs.
- `.pytest_cache/`, `__pycache__/`, and `.pyc` files: test/interpreter
  artifacts.
- `osm2terrn.egg-info/`: local package metadata/build artifact.
- `.env`: ignored local environment file; do not index values or contents.

`notebooks/osm2tern_notebook.ipynb` is tracked and should be inventoried as a
source notebook, while its stored cell outputs (if any) should be treated
separately from executable source. `scripts/test_write.txt` is a tracked
auxiliary file whose purpose is not clear from its name alone.

## Open questions for the next inspection

1. Is the missing `osm2terrn/cache/` package intentionally absent in this
   working tree, pending work, or supplied through a mechanism outside the
   repository? Static inspection cannot establish the intended resolution.
2. Which elevation provider is intended as the standard path: the configured
   OpenTopoData URL template, or the direct OpenTopography GlobalDEM request?
3. Is the existing `load()` placeholder intended to become a local cache/project
   loader, or is the README describing a planned workflow?
4. Which test command is the maintained baseline: the standalone bbox runner,
   pytest discovery, or another documented workflow? This audit did not run
   any of them.
5. Which files in `.examples/`, `.docs/`, and `output/` are reusable fixtures
   versus generated results? Their contents were intentionally not catalogued.
6. Which entry points/scripts are supported for users and which are developer
   experiments? Names and guards alone do not establish support status.
7. Are the untracked architecture completion note and current modified source
   paths part of an intentional phase of work? This audit does not attribute
   them.

## Suggested scope for the next automated inventory

The next inventory should produce structured records rather than copy every
file's content into documentation. Recommended fields:

- **File identity:** repository-relative path, extension, byte size, Git state
  (tracked/modified/untracked/ignored), and a classification
  (source/test/docs/config/script/data/generated).
- **Python module record:** package/module path, module docstring, imports,
  locally defined classes/functions, signatures, decorators, type annotations,
  docstring presence, and source line locations.
- **Execution graph:** declared entry points, direct-execution guards, module
  imports, important local call edges, and conditional branches/early returns
  on the app → acquisition → validation/adaptation → processing → export
  route. Mark dynamic imports and external calls separately.
- **Domain/data contracts:** entity/value-object definitions, config model
  fields/defaults, project YAML keys, conversion/adaptation functions, and
  exporter input/output shapes.
- **External integrations:** provider/library, call-site path and symbol,
  network operation or SDK, environment-variable *name*, and whether a call is
  conditional or cached. Never collect key/token values.
- **Test mapping:** pytest file and test function, referenced source symbols,
  fixture/setup dependencies, external-service mocking, and whether a test is
  marked or structured as a standalone runner. Do not imply a test passed
  without execution evidence.
- **Documentation cross-reference:** documented path/symbol, resolved source
  path/symbol if any, and status such as current, stale, missing, or
  unverifiable.
- **Exclusion metadata:** ignored paths, virtual environments, caches, logs,
  generated outputs, compiled files, binary/large datasets, and local secret
  files. Record only categories and safe metadata, not contents.

Keep observations, inferred relationships, and unresolved questions in
separate fields. A source-level inventory should also flag missing imports and
unresolved references for manual confirmation rather than silently treating
them as valid architecture.
