# OSM2terrn Project Roadmap

This document outlines the planned development phases and goals for **OSM2terrn**. It serves as a guide for contributors and helps track the project's progress.

---

## Milestone 1 - Core Functionality (In Progress)
Focus on the essential features to generate basic terrains for Rigs of Rods.

### Tasks:
- [x] Download and parse OSM data (roads, rivers, power lines).
- [x] Fetch elevation data via OpenTopoData API.
- [x] Generate basic .terrn2 files.
- [ ] Export .odef files for objects (buildings, poles).
- [x] Heightmap generation (grayscale PNGs).
- [ ] CLI Interface for online/offline modes.

---

## Milestone 2 - Advanced Features (Planned)
Enhance realism and add visual details to terrains.

### Tasks:
- [ ] Texture splatting (asphalt, grass, dirt layers).
- [ ] Building geometry export (simple shapes).
- [ ] Object placement (trees, traffic signs, street lights).
- [ ] Add support for custom object definitions (.odef templates).
- [ ] Visual preview/validation tool (optional).

---

## Milestone 3 - Optimization & Community Tools (Future)
Prepare the project for larger maps and collaborative contributions.

### Tasks:
- [ ] Processing optimizations for large datasets.
- [ ] Configurable export profiles (urban, rural, mixed).
- [ ] Implement unit tests and automatic validation scripts.
- [ ] Provide example map projects (ready-to-download packages).
- [ ] Detailed developer documentation.

---

## Long-term Ideas (Suggestions)
These are potential features that may be developed if there's community interest.

- Integration of Overture building footprints.
- Forest/vegetation zone generation.
- Water bodies (lakes, rivers with flow direction).
- Procedural generation of missing road segments.
- Support for RoR vehicle spawnpoints and camera presets.

---

## Contribution Guide
If you're interested in helping with a specific milestone, check the Issues tab for tasks labeled `good first issue` or `help wanted`.

For more complex contributions, it's recommended to discuss your idea in an Issue before starting development.

---

## Current Maintainer
Joako360 - [https://github.com/Joako360](https://github.com/Joako360)