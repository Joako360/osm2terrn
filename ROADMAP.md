# OSM2terrn - Development Roadmap

This document outlines the planned development phases and goals for **OSM2terrn**. It serves as a guide for contributors and helps track the project's progress.

**Last Updated**: February 13, 2026

---

## Phase 1 - Core Infrastructure ✅ (COMPLETED)

Focus on essential features for generating complete Rigs of Rods terrains.

### Completed Tasks:
- [x] Download and parse OSM data (roads, rivers, power lines)
- [x] Fetch elevation data via OpenTopoData API
- [x] Generate heightmaps (grayscale PNG format)
- [x] Implement BBox-centric geometry handling
- [x] Create modular exporter architecture
- [x] Procedural road network export (.tobj)
- [x] Generate .terrn2 entry point files
- [x] Create .otc geometry configuration
- [x] Implement ground texture splatting
- [x] CLI interface with interactive menus
- [x] Centralized logging system
- [x] Unit tests for core utilities

---

## Phase 2 - Enhanced Terrain Details 🚧 (IN PROGRESS)

Enhance realism with advanced features and visual polish.

### In Progress:
- [x] Texture splatting implementation (partial)
- [x] Terrain geometry optimization
- [ ] Building footprint export (from OSM data)
- [ ] Advanced texture blending options
- [ ] Support for water body generation
- [ ] Forest/vegetation zone support

### Next Steps:
- [ ] Building placement with height data
- [ ] Traffic sign and street light objects
- [ ] Custom object definition (.odef) templates
- [ ] Railroad track generation (rail_track_formatter.py foundation exists)
- [ ] Power line visualization
- [ ] Performance optimization for large terrains

---

## Phase 3 - Performance & Community Tools 📋 (PLANNED)

Optimize for larger maps and provide community resources.

### Planned Tasks:
- [ ] Performance profiling and optimization
- [ ] Parallel processing for large datasets
- [ ] Configurable export profiles (urban, rural, industrial, mixed)
- [ ] Expand unit test coverage
- [ ] Automated validation and error reporting
- [ ] Provide pre-built example terrains
- [ ] Create comprehensive API documentation
- [ ] Implement progress bars and status reporting
- [ ] Support for batch processing
- [ ] Cache management and cleanup utilities
- [ ] Docker containerization

---

## Phase 4 - Advanced Features 💡 (FUTURE)

Long-term enhancements based on community interest and technical feasibility.

### Potential Features:
- Integration with Overture building footprints for detailed data
- Advanced forest/vegetation zone generation with density mapping
- Water body modeling (lakes, rivers with flow direction)
- Procedural completion of missing road segments
- Support for RoR vehicle spawnpoints and camera presets
- Heightfield smoothing and terrain enhancement filters
- Integration with historical map data (time-based terrain generation)
- Multiplayer terrain synchronization utilities
- Web-based UI for terrain preview and configuration
- Plugin system for custom data sources
- Integration with Mapbox and other tile providers
- Support for satellite imagery as terrain texture overlay
- Machine learning-based terrain classification
- Automatic building height estimation from OSM data

---

## Technical Debt & Maintenance

### Current Focus Areas:
- Code documentation completeness
- Test coverage expansion
- Performance profiling and optimization
- Dependency version management
- API stability and backward compatibility

### Known Limitations:
- Large maps (>100km²) may require significant processing time
- Rasterio depends on system GDAL installation
- Some OSM data may be incomplete or outdated in certain regions
- Elevation data resolution limited by OpenTopoData API

---

## Contribution Guidelines

### Getting Started:
1. **Explore** the [Issues](https://github.com/Joako360/osm2terrn/issues) tab
2. **Look for** labels: `good first issue`, `help wanted`, `enhancement`
3. **Read** [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
4. **Review** `.github/copilot-instructions.md` for code standards

### For Major Features:
1. Open a GitHub Issue to discuss your idea
2. Wait for feedback from maintainers
3. Create a detailed PR with clear description
4. Ensure all tests pass and code follows standards

### Areas Welcome for Contributions:
- **Documentation**: More examples, tutorials, API docs
- **Testing**: Unit tests, integration tests, edge cases
- **Performance**: Optimization and profiling
- **Features**: New exporters, data sources, visualizations
- **Bug Fixes**: Issues labeled `bug`
- **Accessibility**: Better error messages, logging

---

## Release Schedule

The project follows a flexible release schedule:

| Version | Status | Features |
|---------|--------|----------|
| v0.3.0  | ✅ Current | BBox refactor, modular exporters, enhanced CLI |
| v0.4.0  | 🚧 Next | Building export, advanced texturing |
| v0.5.0  | 📋 Planned | Performance optimization, batch processing |
| v1.0.0  | 💡 Future | Production-ready release |

---

## How We Use Issues

**Labels** help organize work:
- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Docs need updating
- `good first issue` - Great for beginners
- `help wanted` - Maintainers need assistance
- `discussion` - General discussion
- `wontfix` - Won't be worked on

---

## Project Governance

**Lead Maintainer**: Joako360 - [GitHub](https://github.com/Joako360)

**Decision Making**:
- Feature requests discussed via Issues
- Major changes require community feedback
- PRs reviewed for code quality and consistency

**Support**:
- 📖 Documentation: [README.md](README.md), [docs/](docs/)
- 🐛 Bug Reports: [Issues](https://github.com/Joako360/osm2terrn/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Joako360/osm2terrn/discussions)
- 🤝 Contributions: Via Pull Requests

---

## License

This project is licensed under **GNU General Public License v3.0 (GPLv3)**.

See [LICENCE.txt](LICENCE.txt) for full license text.