# OSM2terrn - Realistic Map Generator for Rigs of Rods

OSM2terrn is an open-source Python project that generates realistic terrains for the driving simulator **Rigs of Rods**, using real-world data from **OpenStreetMap (OSM)** and **OpenTopoData**.

The project processes geographic data (roads, elevation, etc.) and outputs Rigs of Rods-compatible **heightmaps (.png)** and files ready for manual editing.

---

## Features

- Download and process **OSM data** (roads, rivers, power lines).
- Obtain **elevation data** from OpenTopoData.
- Generate **heightmaps (PNG)** ready for Rigs of Rods.
- Modular structure for future expansions (textures, objects, etc.).
- Simple **Command Line Interface (CLI)**.

---

## Project Structure

```
osm2terrn/
├── main.py                        # Main entry point (CLI runner)
├── data/
│   └── osm_data_handler.py        # Downloads and parses OSM data
├── processing/
│   ├── heightmap_handler.py       # Handles elevation data and heightmap export
│   └── texture_splatting.py       # (Optional) Texture splatting logic
├── utils/
│   ├── geometry.py                # Coordinate conversions and geometry utils
│   ├── io_utils.py                # File I/O helpers
│   └── logger.py                  # Simple logger function
├── scripts/
│   └── generate_example.py        # Example automation script
├── requirements.txt               # Python dependencies
└── README.md
```

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Joako360/osm2terrn.git
cd osm2terrn
```

2. Install the required Python libraries:

```bash
pip install -r requirements.txt
```

---

## Usage

Run the CLI tool:

```bash
python main.py
```

Steps:

1. Enter the bounding box coordinates (W, S, E, N).
2. The program will download OSM data and elevation data.
3. A heightmap (.png) will be generated and exported.

---

## Roadmap (Simplified)

### Core Features (Done)

- Download and parse OSM data.
- Fetch elevation data.
- Generate and export heightmaps.

### Upcoming

- Texture splatting (grass, asphalt, dirt).
- Export object placements (buildings, poles).
- Optimization for larger maps.

### Long-term Ideas

- Procedural object generation.
- Visual validation tools.
- Community-contributed map templates.

---

## Contributing

This is a community-driven project. Contributions are welcome! Check the CONTRIBUTING.md for guidelines.

---

## License

This project is licensed under **GNU General Public License v3.0 (GPLv3)**.

---

## Author

Developed by [Joako360](https://github.com/Joako360)

---

## Disclaimer

This project is unofficial and not affiliated with Rigs of Rods developers. It is provided as-is for community use.

