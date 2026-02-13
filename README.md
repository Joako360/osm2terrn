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
- 📊 Obtain **elevation data** from OpenTopoData API.
- 🗺️ Generate **heightmaps (PNG)** with automatic size optimization.
- 🛣️ Export **procedural road networks** (.tobj format).
- 🎨 Apply **texture splatting** for terrain detail layers.
- 📐 Create complete **terrain packages** (.terrn2 + .otc + .tobj).
- 🔧 **Modular architecture** for easy extension and maintenance.
- ⚡ **Robust CLI interface** with interactive menus.

---

## Project Structure

```
osm2terrn/
├── main.py                           # CLI entry point with interactive menu
├── src/
│   ├── data/
│   │   ├── osm_data_handler.py       # OSM data download and parsing
│   │   └── osm_loader.py             # OSM graph loading utilities
│   ├── processing/
│   │   ├── heightmap_handler.py      # Elevation data and heightmap generation
│   │   ├── otc_exporter.py           # .otc terrain geometry export
│   │   ├── terrn2_exporter.py        # .terrn2 entry point export
│   │   ├── tobj_exporter.py          # .tobj objects/roads export
│   │   ├── road_network_formatter.py # Road network processing pipeline
│   │   ├── road_exporters.py         # Road export utilities
│   │   ├── road_merger.py            # Road merging and optimization
│   │   ├── road_model.py             # Road data structures
│   │   ├── texture_splatting.py      # Texture layer blending
│   │   └── rail_track_formatter.py   # Railroad track support
│   └── utils/
│       ├── bbox.py                   # BBox class for bounds handling ⭐
│       ├── geometry.py               # Coordinate transformations
│       ├── geometry_utils.py         # Advanced geometry operations
│       ├── io_utils.py               # File I/O helpers
│       ├── logger.py                 # Centralized logging
│       ├── constants.py              # Global constants and defaults
│       └── visualization.py          # Visualization utilities
├── tests/
│   ├── test_bbox.py                  # BBox unit tests
│   └── run_bbox_tests.py             # Test runner
├── scripts/
│   └── *.py                          # Example automation scripts
├── docs/
│   ├── exporters-docs.md             # Exporter format specifications
│   └── ...
├── .github/
│   ├── copilot-instructions.md       # Copilot development guidelines
│   └── instructions/
│       └── exporters.instructions.md # Exporter format rules
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
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
- Elevation data fetched from OpenTopoData API

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
- `*groundmap.png` - Texture detail

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

## Project Status

### ✅ Completed

- [x] OSM data download and parsing
- [x] Elevation data fetching (OpenTopoData)
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
         → Terrain Config (TERRN2/OTC)
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

- 📖 **Documentation**: See [ROADMAP.md](ROADMAP.md) and [docs/](docs/)
- 🐛 **Bug Reports**: [Issues](https://github.com/Joako360/osm2terrn/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Joako360/osm2terrn/discussions)
- 📧 **Contact**: Via GitHub issues

---

## Disclaimer

This project is **unofficial** and not affiliated with Rigs of Rods developers. It is provided as-is for community use.

**Attribution**: OSM data © OpenStreetMap contributors, available under ODbL license.

