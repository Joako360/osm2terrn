# OSM2terrn - Realistic Map Generator for Rigs of Rods

OSM2terrn is an open-source Python project that generates realistic terrains for the driving simulator **Rigs of Rods** (RoR), using real-world data from **OpenStreetMap (OSM)** and **OpenTopoData**.

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
pip install -r requirements.txt
```

---

## Quick Start

### 1. Run the CLI

```bash
python main.py
```

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
- Select a city (search by name) or enter custom bounding box
- System downloads OSM data (roads, terrain features)
- Elevation data fetched from OpenTopography API

**Step 2: Process**
- Roads are merged and optimized
- Heightmap generated from elevation data
- Texture splatting applied for detail

**Step 3: Export**
- `.terrn2` - Terrain entry point
- `.otc` - Terrain geometry configuration
- `-page-0-0.otc` - Paging configuration
- `.tobj` - Procedural roads and objects
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

### ✅ Completed

- [x] OSM data download and parsing
- [x] Elevation data fetching (OpenTopography)
- [x] Heightmap generation (PNG format)
- [x] Ground texture splatting
- [x] Procedural road network export (.tobj)
- [x] Terrain configuration (.terrn2)
- [x] OTC geometry export (.otc pages)
- [x] BBox-centric coordinate handling
- [x] Modular exporter architecture
- [x] Unit tests for core utilities

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

See [ROADMAP.md](ROADMAP.md) for detailed timeline.

---

## Architecture & Design

### Core Components

**BBox (Bounding Box) ⭐**
- Centralized bounds handling with automatic CRS detection
- Supports multiple input formats (dict, tuple, GeoDataFrame, shapely)
- Ensures coordinate consistency across the project
- Used in all geometry operations

**Data Pipeline**
```
OSM (via OSMnx) → Geometry Processing → Road Network → Export (TOBJ)
     ↓
Elevation API → Heightmap Generation → Texture Splatting → Export (PNG)
     ↓
Terrain Config (TERRN2/OTC)
```

### Exporter Modules
- `terrn2_exporter.py` - Creates .terrn2 entry point
- `otc_exporter.py` - Creates .otc geometry configuration
- `tobj_exporter.py` - Exports objects and procedural roads
- `heightmap_handler.py` - Manages raster generation
- `road_network_formatter.py` - Orchestrates road pipeline

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
python tests/run_bbox_tests.py
```

### Code Standards

- **Python**: 3.10+
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
2. **Review** [ROADMAP.md](ROADMAP.md) for priorities
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

- 📖 **Documentation**: See [ROADMAP.md](ROADMAP.md) and [.docs/](.docs/)
- 🐛 **Bug Reports**: [Issues](https://github.com/Joako360/osm2terrn/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Joako360/osm2terrn/discussions)
- 📧 **Contact**: Via GitHub issues

---

## Disclaimer

This project is **unofficial** and not affiliated with Rigs of Rods developers. It is provided as-is for community use.

**Attribution**: OSM data © OpenStreetMap contributors, available under ODbL license.
