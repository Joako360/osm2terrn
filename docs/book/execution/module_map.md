# Module and Data-Responsibility Map

This map describes responsibilities visible in imports and direct calls. It
does not assert that every module participates in every invocation.

## Current source update — 2026-11-07

The current acquisition boundary includes `osm2terrn/data/acquisition.py`,
`overpass.py`, and `street_network.py`; the current street handoff is recorded
in `data-handoff-analysis.md`. These files are present in the current working
tree and are included by the refreshed static inventory. The rows below retain
the earlier map and any historical route descriptions; use the dated update
where they conflict. Presence in the map does not prove runtime use by every
route.

The road bullets below contain the historical Stage 3.2 route. The dated
street-handoff follow-up at the end records the current implementation.

| Module/file | Responsibility evidenced in source | Main connections / data |
|---|---|---|
| `osm2terrn/app/main.py` | Parser, CLI override construction, config loading, menu startup. | `argparse`, `config.loader`, `config.settings`, then `cli.menu`. |
| `osm2terrn/config/loader.py` | Default/project file reading, includes, precedence merge, typed validation. | ProgramConfig and ProjectConfig models. Formats handled by suffix: JSON, TOML, YAML. |
| `osm2terrn/config/settings.py` | Process-level accessors and stored config objects. | `configure`, `get_program_config`, `get_project_config`. |
| `osm2terrn/cli/menu.py`, `cli/components.py` | Menu option data, interactive dispatch, rendering/input. | Callbacks from `cli.commands`. |
| `osm2terrn/cli/commands.py` | Download, placeholder load, export and exit actions; owns calls into state/providers/orchestration. | `current_map`, `download_data_from_bbox`, elevation fetch, `export_terrain_assets`. |
| `osm2terrn/app/app_state.py` | Mutable current-session map state used by the CLI actions. | Place, downloaded dict (the returned bundle contains bounds), origin and elevation data. |
| `osm2terrn/data/download_menu.py` and `download_menu_components.py` | Interactive search/custom-bbox selection and Nominatim result conversion. | OSMnx private `_nominatim` request API and `BoundingBox` tuple shape. |
| `osm2terrn/data/osm_data_handler.py` | Bbox-based OSM features/networks, caching, coordinate transform and partial failure handling. | OSMnx, cache manager, GeoDataFrames/graphs, RoR coordinate adapters. |
| `osm2terrn/data/osm_loader.py` | Separate place/bbox graph loading and conversion of graph edges to line geometries. | OSMnx, NetworkX, GeoPandas/Shapely types. Used by `build_roads_from_place`. |
| `osm2terrn/cache/` | Cache manager, key, metadata and serializers used by OSM, elevation, map-data and image processing paths. | Pickle-based cached bundles/raster/MapData; cache hits bypass provider/processing paths. |
| `osm2terrn/domain/value_objects/` and `domain/entities/` | Typed coordinates, bounds, polylines, roads/buildings/map aggregate. | Adapter inputs and outputs; exact semantics belong to their source docs. |
| `osm2terrn/domain/adapters/bounds.py` | Coerces accepted bounds representations to domain `BoundingBox`. | Called before coordinate-sensitive operations. |
| `osm2terrn/domain/adapters/osmnx_to_map.py` | Builds `MapData`; converts `roads_gdf` only when supplied. | `roads_gdf=None` produces an empty roads list in the current implementation. |
| `osm2terrn/processing/terrain/elevation_service.py` | OpenTopography raster query, cache, raster decoding and sampling helper. | `requests`, rasterio, NumPy, API key from configured environment-variable name. |
| `osm2terrn/processing/terrain/heightmap_handler.py` | Normalize/prepare elevation, smoothing/cache and image writes. | NumPy, SciPy, Pillow, colormap renderer; fetch fallback if no usable elevation dict. |
| `osm2terrn/processing/orchestrator.py` | Coordinates MapData construction and export of image, roads, OTC, TOBJ manifest and TERRN2. | Terrain, network, domain adapter, bounds utilities. |
| `osm2terrn/processing/network/road_network_export.py` | Builds road segments/objects from a place graph, local CRS, elevation/intersections and TOBJ export. | `osm_loader`, geometry/elevation helpers, `TobjExporter`. Re-fetches graph by place. |
| `osm2terrn/processing/otc/` and `processing/terrain/terrn2_entrypoint.py` | Write page/global OTC and terrain entry-point text. | File outputs and computed world/elevation parameters. |

## Important boundaries in the currently wired route

- The download command obtains a dictionary of OSM geometries/networks and
  stores it on `current_map.data`.
- The export callback passes only selected fields from `current_map` to the
  orchestrator. The orchestrator calls the MapData adapter without
  `roads_gdf`, and the adapter therefore constructs `roads=[]`.
- `_export_roads()` consumes domain road entities, not the earlier OSM bundle;
  if supplied nonempty roads it loads another graph by place through
  `build_roads_from_place()`.
- The domain-object manifest writes comments with road/building counts and
  attributes from the constructed MapData. It is not itself a serializer of
  the raw downloaded OSM dictionary.

These points are code facts from `osm2terrn/cli/commands.py:32-109`,
`osm2terrn/processing/orchestrator.py:187-275`,
`osm2terrn/domain/adapters/osmnx_to_map.py:54-105`,
`osm2terrn/processing/network/road_network_export.py:40-60`, and
`osm2terrn/processing/orchestrator.py:57-124`.

## Street handoff after implementation — 2026-10-20

`osm2terrn/data/street_network.py` defines the acquisition result and its
explicit states. `osm2terrn/domain/adapters/osmnx_to_roads.py` creates the
EPSG:4326 `MapData` view from the canonical graph. The orchestrator forwards
the graph to `build_roads_from_graph()` for procedural road output; the
place-based builder remains a compatibility wrapper. `data-handoff-analysis.md`
records synthetic evidence and the remaining real-provider limitations.
