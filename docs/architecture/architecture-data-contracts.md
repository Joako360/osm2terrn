# Architecture: current data boundaries

The table records source-level interfaces, not guarantees about provider
success. See the [execution evidence register](../book/execution/evidence_register.md)
and [open uncertainties](../book/execution/uncertainties.md) for scoped
locators and verification state.

| Boundary | Current source representation | Evidence location |
|---|---|---|
| Area input | Place label and/or bounds selected in the CLI; current download callback rejects a missing place label before invoking the bbox downloader | `osm2terrn/data/download_menu.py`; `osm2terrn/cli/commands.py` |
| OSM acquisition | Bundle containing bounds, feature/network values and acquisition outcomes; street network is represented by `StreetNetworkResult` | `osm2terrn/data/osm_data_handler.py`; `osm2terrn/data/acquisition.py`; `osm2terrn/data/street_network.py` |
| Street network | Canonical OSMnx/NetworkX graph plus explicit status/CRS metadata; adapter creates the geometry expected by `MapData` | `osm2terrn/data/street_network.py`; `osm2terrn/domain/adapters/osmnx_to_map.py`; `osm2terrn/processing/orchestrator.py` |
| Elevation | Elevation service returns raster data consumed by heightmap processing; provider/cache behavior is branch-dependent | `osm2terrn/processing/terrain/elevation_service.py`; `osm2terrn/processing/terrain/heightmap_handler.py` |
| Domain map | Typed map/domain entities assembled by adapters from acquisition and processing values | `osm2terrn/domain/entities/`; `osm2terrn/domain/adapters/` |
| Terrain output | Raster images, OTC files, TOBJ objects and TERRN2 entry point assembled by processing/orchestration | `osm2terrn/processing/orchestrator.py`; `osm2terrn/processing/terrain/`; `osm2terrn/processing/network/` |

`export.include_roads` is parsed and currently gates the road path in the
orchestrator. Requested building export reports an unimplemented outcome.
Do not interpret an empty layer as an acquisition error: acquisition statuses
distinguish `not_requested`, `empty`, `available` and `failed` in the current
data model.

CRS conversions must use explicit transformations in the source. A CRS label
or metadata field by itself is not evidence that coordinate values were
transformed. The streets-specific contract and unresolved coordinate questions
are maintained in [`data-handoff-analysis.md`](../book/execution/data-handoff-analysis.md).
