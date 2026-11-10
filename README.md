# OSM2terrn - Realistic Map Generator for Rigs of Rods

OSM2terrn is an open-source Python project for generating terrain assets for the **Rigs of Rods** (RoR) simulator from geospatial data. The current package declares OpenStreetMap/OSMnx, OpenTopography and Overture Maps related integrations; exact active paths and verification status are documented in [the architecture guide](docs/architecture/architecture-index.md) and [the execution map](docs/book/execution/README.md).

The project processes geographic data (roads, elevation, terrain) and outputs Rigs of Rods-compatible files:
- **heightmaps (.png)** - Terrain elevation data
- **.terrn2** - Terrain entry point configuration  
- **.otc** - Terrain geometry and page configuration
- **.tobj** - Terrain objects and procedural roads
- **Ground textures** - Splatted terrain layers

---

## Features

- 📥 Download and process **OSM data** (roads, rivers, power lines, terrain).
- 📊 Obtain **elevation data** from OpenTopography API.
- 🗺️ Generate **heightmaps (PNG)** with automatic size optimization.
- 🛣️ Generate **procedural road networks** (.tobj format).
- 🎨 Apply **texture splatting** for terrain detail layers.
- 📐 Export complete **terrain packages** (.terrn2 + .otc + .tobj).
- 🔧 **Modular architecture** for easy extension and maintenance.
- ⚡ **Robust CLI interface** with interactive menus.

---

## Project Structure

```
osm2terrn/
├── osm2terrn/
│   ├── app/            # Application entry point and session state
│   ├── cli/            # Interactive menu and commands
│   ├── config/         # Centralized configuration system ⭐
│   ├── data/           # OSM data acquisition and loading
│   ├── domain/         # Typed domain models and adapters
│   ├── processing/     # Terrain, roads, OTC and network exporters
│   └── utils/          # Shared utilities (logging, coordinates, bbox…)
├── projects/
│   └── template/       # Starter project — copy and customize
├── tests/              # pytest unit tests
├── docs/               # Extended documentation
└── output/             # Generated terrain files (gitignored)
```

---

## Installation

### Prerequisites
- Python 3.12 or higher
- pip package manager
- GDAL/Rasterio system dependencies (usually installed via pip)

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/Joako360/osm2terrn.git
cd osm2terrn
```

2. **Create virtual environment (recommended):**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

3. **Install dependencies:**

```bash
pip install .
```

For development dependencies, install the `dev` extra declared in
`pyproject.toml` with `pip install -e ".[dev]"`.

---

## Quick Start

### 1. Run the CLI

```bash
python -m osm2terrn
```

The package also declares the `osm2terrn` console script. These are declared
launch routes; installation and execution are not implied.

### 2. Interactive Menu

The CLI provides an interactive menu:

```
╔════════════════════════════════════════╗
║      OSM2terrn - Main Menu             ║
╠════════════════════════════════════════╣
║  1. Download map data (OSM + Elevation)║
║  2. Load cached data                   ║
║  3. Process and export terrain         ║
║  4. Exit                               ║
╚════════════════════════════════════════╝
```

### 3. Workflow

**Step 1: Download**
- The menu offers place search and manual bounds. In the current source route,
  the manual-bounds result has an empty place label and is rejected by the
  download callback; do not assume that route completes.
- For selections accepted by the callback, OSM acquisition uses configured
  layers; individual layers may be empty or fail independently.
- Elevation acquisition through the OpenTopography service path (provider
  success depends on configuration and network availability)

**Step 2: Process**
- Roads are merged and optimized
- Heightmap generated from elevation data
- Texture splatting applied for detail

**Step 3: Export**
- `.terrn2` - Terrain entry point
- `.otc` - Terrain geometry configuration
- `-page-0-0.otc` - Paging configuration
- `.tobj` - Terrain objects and, when enabled and available, procedural roads
- `*heightmap.png` - Elevation raster
- `*groundmap.png` - Terrain rendering (Simulated Satellite Image)

### 4. Output Files

All files generated in `output/` directory:

```
output/
├── MyTerrain_heightmap.png
├── MyTerrain_groundmap.png
├── MyTerrain_roads.tobj
├── MyTerrain.terrn2
├── MyTerrain.otc
└── MyTerrain-page-0-0.otc
```

---

## Configuration

osm2terrn uses a centralized YAML configuration system.  
Every parameter has a single source of truth; no hardcoded values exist in business logic.

### Precedence order (lowest → highest)

| Layer | Origin | How to supply |
|-------|--------|---------------|
| 1 | **Defaults** | Built into the program (`config/defaults.py`) |
| 2 | **Project files** | `project.yaml` + any `includes:` fragments |
| 3 | **CLI arguments** | Flags passed to `osm2terrn` at launch |
| 4 | **Interface / API** | Programmatic injection via `configure()` |

A later layer always wins over an earlier one.

### Using a project

```bash
# Launch with a specific project directory
python -m osm2terrn --project-dir projects/my_city/

# Or point to a single config file
python -m osm2terrn --config-file projects/my_city/project.yaml
```

The project directory is auto-detected from the environment variable `OSM2TERRN_PROJECT_DIR` as well.

### Anatomy of a project

```
projects/
└── my_city/
    ├── project.yaml    ← entrypoint; may include other files
    ├── terrain.yaml
    ├── roads.yaml
    ├── buildings.yaml
    ├── materials.yaml
    ├── export.yaml
    └── pipeline.yaml
```

Copy `projects/template/` as a starting point.

#### project.yaml (entrypoint)

```yaml
# includes merges files before this file is applied
includes:
  - terrain.yaml
  - roads.yaml
  - buildings.yaml
  - materials.yaml
  - export.yaml
  - pipeline.yaml

export:
  output_name: my_city
```

#### terrain.yaml

```yaml
terrain:
  page_size: 1025          # heightmap size in pixels (2^n + 1)
  output_size: [1025, 1025]
  colormap: gist_earth     # groundmap palette: terrain, physical, cet_l10…
  smoothing_sigma: 1.0     # gaussian smoothing (0 = none)
```

#### roads.yaml

```yaml
roads:
  network_type: drive      # drive | walk | bike | all
  simplify: true
  default_width: 7.0       # metres
  default_border_width: 0.0
  default_border_height: 0.0
```

#### buildings.yaml / materials.yaml / export.yaml / pipeline.yaml

```yaml
buildings:
  enabled: true

materials:
  default_ground_texture: terrain_detail.dds

export:
  include_roads: true
  include_buildings: true

pipeline:
  preload_elevation: true
```

### CLI overrides (layer 3)

Any project value can be overridden at launch without editing files:

```bash
python -m osm2terrn \
  --project-dir projects/my_city/ \
  --terrain-page-size 2049 \
  --terrain-colormap physical \
  --roads-network-type all \
  --roads-no-simplify \
  --export-output-name custom_name \
  --output-dir /tmp/output
```

Full list of flags:

| Flag | Description |
|------|-------------|
| `--project-dir PATH` | Project directory to load |
| `--config-file PATH` | Single config file to load |
| `--output-dir PATH` | Override output directory |
| `--logs-dir PATH` | Override logs directory |
| `--cache-dir PATH` | Override cache directory |
| `--terrain-page-size N` | Heightmap resolution |
| `--terrain-output-width W --terrain-output-height H` | Output image size (both required) |
| `--terrain-colormap NAME` | Ground texture colormap |
| `--terrain-smoothing-sigma F` | Gaussian sigma |
| `--roads-network-type TYPE` | OSM network type |
| `--roads-simplify / --roads-no-simplify` | Road graph simplification |
| `--roads-default-width F` | Default road width (m) |
| `--export-output-name NAME` | Base name for output files |
| `--export-include-roads / --export-no-include-roads` | Include roads in export |
| `--export-include-buildings / --export-no-include-buildings` | Include buildings |
| `--pipeline-preload-elevation / --pipeline-no-preload-elevation` | Preload DEM on download |

### Using includes

A project file can include other YAML files.  
Useful for sharing base settings across projects:

```yaml
# projects/my_city/project.yaml
includes:
  - ../shared/base_roads.yaml   # relative paths are supported
  - terrain.yaml

export:
  output_name: my_city
```

Circular includes are detected and raise a `ValueError`.

### Supported config formats

| Format | Extension | Notes |
|--------|-----------|-------|
| **YAML** | `.yaml`, `.yml` | Recommended — hierarchical and readable |
| TOML | `.toml` | Supported; requires Python ≥ 3.11 `tomllib` |
| JSON | `.json` | Supported for programmatic use |

---

## Contributor Learning Path

If you are new and want to contribute, read in this order:

1. [CONTRIBUTING.md](CONTRIBUTING.md)
2. [Contributor onboarding guide (English)](docs/contributor-onboarding-en.md) or [Contributor onboarding guide (Spanish)](docs/contributor-onboarding-es.md)
3. [Contributor docs index (short, topic-focused pages)](docs/README.md)
4. [Architecture index](docs/architecture/architecture-index.md)
5. [CLI flow index](docs/cli-flow/cli-index.md)
6. [Function reference index](docs/function-reference/function-reference-index.md)
7. [Troubleshooting index](docs/troubleshooting/troubleshooting-index.md)
8. [Testing and validation index](docs/testing-validation/testing-index.md)
9. [Exporter docs](docs/exporters-docs.md)
10. [OpenTopography API key setup (English)](docs/opentopography-api/opentopography-api-key-en.md) or [OpenTopography API key setup (Spanish)](docs/opentopography-api/opentopography-api-key-es.md)
11. [Realistic Elevation Adjustments (English)](docs/elevation-realism/elevation_realism_improvements-en.md) or [Ajustes de Elevación Realista (Spanish)](docs/elevation-realism/elevation_realism_improvements-es.md)

## Project Status

### Implementation areas (not equivalent to end-to-end verification)

- Source modules for acquisition, terrain processing and export are present.
  Presence and focused synthetic tests do not establish end-to-end provider or
  simulator behavior.
- Dated bounded runs and their limitations are recorded in the [first](docs/book/validation/first_geographic_validation.md)
  and [second](docs/book/validation/second_geographic_validation.md) geographic
  validation reports.

### 🚧 In Progress

- [ ] Building/object placement
- [ ] Advanced texture blending
- [ ] Performance optimization
- [ ] Extended documentation

### 📋 Planned

- [ ] Building footprint export
- [ ] Forest/vegetation generation
- [ ] Water body support
- [ ] Visual preview tool
- [ ] RoR vehicle spawnpoints

See [the documentation index](docs/README.md) for maintained guides and
current verification status.

---

## Architecture & Design

### Source organization (observed package layout)

The application source is organized under `osm2terrn/` into app, CLI,
configuration, data, domain, processing, and utility packages. This describes
current paths, not full realization of the aspirational ADRs. See the
[source-based execution map](docs/book/execution/README.md) for the route and
open questions.

Current high-level route (static call path; not a runtime guarantee):
```
OSM (via OSMnx) → Geometry Processing → Road Network → Export (TOBJ)
     ↓
Elevation API → Heightmap Generation → Texture Splatting → Export (PNG)
     ↓
Terrain Config (TERRN2/OTC)
```

Processor and exporter locations are listed in
[the architecture module map](docs/architecture/architecture-modules.md).

### Design Principles

- 🔧 **Modularity**: Single responsibility per component
- 📋 **Consistency**: Local UTM coordinates throughout
- 🔍 **Transparency**: Comprehensive logging
- ✅ **Validation**: Output validation against specs
- 📖 **Documentation**: PEP257 docstrings

---

## Development & Testing

### Run Tests

```bash
python -m pytest
```

### Code Standards

- **Python**: 3.12+
- **Style**: PEP8
- **Docstrings**: PEP257
- **Type Hints**: Recommended

### Logging

Use the centralized logger:

```python
from utils.logger import get_logger, log_info

logger = get_logger("module_name")
log_info(logger, "Your message here")
```

---

## Contributing

This is a community-driven project. Contributions are welcome!

1. **Read** [CONTRIBUTING.md](CONTRIBUTING.md)
2. **Review** the maintained guides in [docs/](docs/README.md) and confirm priorities with maintainers
3. **Check** `.github/copilot-instructions.md` for standards
4. **Create** a fork and submit a pull request

### Issue Labels
- `good first issue` - Beginner-friendly
- `help wanted` - Need assistance
- `enhancement` - Feature request
- `bug` - Bug report

---

## License

This project is licensed under **GNU General Public License v3.0 (GPLv3)**.

See [LICENCE.txt](LICENCE.txt) for full terms.

---

## Author & Maintainer

**Joako360** - [GitHub Profile](https://github.com/Joako360)

---

## Support

- 📖 **Documentation**: See [the documentation index](docs/README.md)
- 🐛 **Bug Reports**: [Issues](https://github.com/Joako360/osm2terrn/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Joako360/osm2terrn/discussions)
- 📧 **Contact**: Via GitHub issues

---

## Disclaimer

This project is **unofficial** and not affiliated with Rigs of Rods developers. It is provided as-is for community use.

**Attribution**: OSM data © OpenStreetMap contributors, available under ODbL license.
