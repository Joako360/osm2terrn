# Architecture: change map

This is a navigation aid, not proof that a planned subsystem is implemented.
Recheck the current source before changing a path.

- CLI workflow → `osm2terrn/app/main.py`, `osm2terrn/cli/commands.py`, `osm2terrn/cli/menu.py`.
- OSM acquisition → `osm2terrn/data/osm_data_handler.py`, `osm2terrn/data/overpass.py`.
- Elevation/raster → `osm2terrn/processing/terrain/elevation_service.py`, `heightmap_handler.py` in that package.
- Bounds and CRS → `osm2terrn/domain/adapters/bounds.py`, `osm2terrn/utils/geometry/`.
- OTC/TERRN2 output → `osm2terrn/processing/terrain/` and `osm2terrn/processing/orchestrator.py`.
- Roads → `osm2terrn/data/street_network.py`, `osm2terrn/domain/adapters/`, `osm2terrn/processing/network/`, `osm2terrn/processing/roads/`.

See the [current architecture map](architecture-modules.md) and
[source execution map](../book/execution/README.md) for evidence qualifications.
