# Call Paths by Application Route

## Current status — 2026-11-07

The sections below preserve the historical Stage 3 source reconstruction. The
current street route now passes the stored `StreetNetworkResult` from
`osm2terrn/cli/commands.py:export` into
`osm2terrn/processing/orchestrator.py:export_terrain_assets`, then adapts the
canonical graph for `MapData` and graph-based road processing. This handoff has
synthetic-test evidence but was not executed against a live provider in this
documentation task. `export.include_roads` gates the road path. Current
download/export details and remaining questions are in
[`README.md`](README.md) and [`data-handoff-analysis.md`](data-handoff-analysis.md).

All routes below are reconstructed from source and static relations. An arrow
means that the cited code calls or dispatches to the next step; it does not
mean that the branch ran in a real session.

The route descriptions below are the historical baseline from before the
street-handoff implementation. The current street path is summarized in the
dated follow-up at the end of this document and documented in detail in
`data-handoff-analysis.md`.

## Startup and menu dispatch

```text
console script / python -m osm2terrn / start.bat
  -> osm2terrn.app.main:main
     -> _build_parser + parse_args
     -> _build_program_cli_overrides
     -> _build_project_cli_overrides
     -> ProjectLoader.load_program_config
     -> ProjectLoader.load_project_config
     -> config.settings.configure
     -> import cli.menu (which imports cli.commands)
     -> mainmenu.run
        -> Menu.run_once -> renderer input -> MenuOption.execute
```

Sources: `pyproject.toml:105-106`; `osm2terrn/__main__.py:1-3`;
`osm2terrn/app/main.py:156-185`; `osm2terrn/config/loader.py:38-97`;
`osm2terrn/config/settings.py:16-85`; `osm2terrn/cli/menu.py:23-115,118-155`.

## Download City action

```text
MainMenuAction.DOWNLOAD_CITY
  -> cli.commands.dlcity
     -> clear + render
     -> data.osm_data_handler.download_menu
        -> DownloadMenu.show_main_menu
           -> search: user text -> search_nominatim -> OSMnx Nominatim request
                     -> select result -> bbox tuple + display name
           -> manual: custom numeric bounds -> (empty place, bbox)
     -> guard: if not place OR not bbox, return without clearing prior session state
     -> download_data_from_bbox(bbox)
        -> normalize/validate bbox; derive center/origin
        -> cache lookup
        -> for configured geometry queries: OSMnx features_from_bbox
        -> for configured network queries: OSMnx graph_from_bbox
        -> transform returned GeoDataFrames/graphs to RoR coordinates
        -> cache bundle and return dict
     -> derive lon/lat origin; compute square bounds
     -> store data/place/origin on app_state.current_map
     -> fetch elevation via heightmapper and store result, or catch and clear it
```

Sources: `osm2terrn/cli/commands.py:21-79`;
`osm2terrn/data/osm_data_handler.py:56-169,172-183`;
`osm2terrn/data/download_menu.py:14-113`;
`osm2terrn/processing/terrain/elevation_service.py:83-140`;
`osm2terrn/app/app_state.py:1-21`.

**Static branch:** the manual selection returns an empty place string, and
`dlcity()` tests `not place`; it therefore returns before the data download.
This early return leaves any prior `current_map` state intact. The city-search
branch is the only branch that supplies both a truthy place and bounding box
to this guard.

`download_data_from_bbox()` uses configured `map_geometries` and `networks`
from program configuration at module import time. For each configured item,
provider errors are caught and that entry is set to `None`; the outer bundle
can still be returned and cached. A cache hit returns its first tuple item
before issuing those provider calls. The exact OSM provider query branch has
not been executed here.

## Load/Import action

`cli.commands.load()` clears the display and prints that loading is “coming
soon” (`osm2terrn/cli/commands.py:82-87`). It does not load cached/project map
data in the inspected implementation. The menu label “Load/Import” is not
evidence of a functioning import path.

## Export action

```text
MainMenuAction.EXPORT
  -> cli.commands.export
     -> current_map.has_data() guard
     -> processing.orchestrator.export_terrain_assets(
          place, bounds, elevation_data, origin_lon, origin_lat, target_bounds)
        -> require domain bounds
        -> build_mapdata_from_pipeline_context(bounds, place, metadata)
        -> generate heightmap + groundmap
           -> use supplied elevation when the required keys exist
           -> otherwise elevation service; on fetch error use flat array
           -> optional smoothing/cache -> save images
        -> _export_roads
           -> no domain roads: set metadata and return None (the UI adapter call
              omits roads_gdf, so on a cache miss it builds an empty road list)
           -> otherwise build_roads_from_place -> OSMnx graph -> geometry,
              elevations/intersections -> TobjExporter
        -> write page OTC; write global OTC
        -> write domain-object .tobj manifest
        -> write .terrn2 entry point
        -> return output-path mapping
```

Sources: `osm2terrn/cli/commands.py:90-115`;
`osm2terrn/processing/orchestrator.py:126-185,187-275`;
`osm2terrn/domain/adapters/osmnx_to_map.py:54-105`;
`osm2terrn/processing/terrain/heightmap_handler.py:44-67,112-178`;
`osm2terrn/processing/terrain/elevation_service.py:83-140`;
`osm2terrn/processing/network/road_network_export.py:40-60,183-196`;
`osm2terrn/processing/otc/otc_paged.py:41-90`;
`osm2terrn/processing/otc/otc_global.py:55-112`;
`osm2terrn/processing/terrain/terrn2_entrypoint.py:102-160`.

### Input/output and failure boundaries

| Stage | Input | Output / transfer | Visible failure behavior |
|---|---|---|---|
| Menu selection | text; city search result or numeric bbox | `(place, bbox)` | Invalid numeric values repeat; invalid bounds recurse to bbox input; provider/Nominatim failures are not caught in `search_nominatim()` itself. |
| OSM bundle | bbox | dict with bounds, origin, geometry/network entries | Per geometry/network provider exceptions become `None`; cache hit short-circuits requests. |
| CLI state | returned dict + place + computed origin | `current_map` fields | Missing `bounds` clears data/elevation and returns; origin conversion errors fall back to `(0,0)`; square-bounds error logs and retains source bounds. |
| Elevation preload | `BoundingBox` | array + max/min in `current_map.elevation_data` | Any exception in `dlcity()` is caught and elevation state becomes `{}`. |
| Heightmap | bounds + optional elevation dict | PNG heightmap, PNG groundmap, elevation stats | Invalid bounds can return `None`; fetch failures become a flat raster; file I/O/image errors beyond the shown catches may propagate. |
| Road export | domain `MapData`, place, origin, bounds | optional roads `.tobj` path | Empty road collection or missing place/origin returns `None`; exceptions in `_export_roads()` are logged and suppressed. |
| Package export | map context + outputs | OTC files, manifest TOBJ, TERRN2, path dict | `cli.commands.export()` catches `Exception`, prints error, and returns to menu. |

No line in this document asserts that any side effect or branch was observed
in a real process.

## Street handoff after implementation — 2026-10-20

The current code passes `current_map.data["roads"]` to
`export_terrain_assets(road_network=...)`. The orchestrator validates the
typed acquisition result, creates a separate EPSG:4326 GeoDataFrame view for
`MapData` when road export is enabled, and passes the canonical graph to
`build_roads_from_graph()` for procedural `.tobj` processing. A supplied graph
is reused for node-elevation fallback. `export.include_roads=false` skips
conversion and road output. These statements describe code and focused
synthetic tests; no interactive session, live OSM query, real terrain, or
final simulator load was performed. See `data-handoff-analysis.md` for exact
status distinctions and verification limits.
