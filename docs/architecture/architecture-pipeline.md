# Architecture: observed source pipeline

This is a source-derived route, not a claim of successful runtime execution.
Separate entry points and fallback branches are documented in the
[book execution map](../book/execution/README.md).

## Interactive application route

1. `osm2terrn.app.main:main` loads configuration and invokes the CLI menu.
2. `osm2terrn.cli.commands.dlcity` obtains an area selection and calls
   `download_data_from_bbox` in `osm2terrn.data.osm_data_handler`.
3. Acquisition returns a bundle with bounds, layer values and acquisition
   outcomes. The CLI stores session data and performs the current elevation
   prefetch path; the parsed `pipeline.preload_elevation` option is not read by
   this callback according to the inspected source.
4. `osm2terrn.cli.commands.export` passes stored bounds, elevation,
   `StreetNetworkResult` and acquisition results to
   `osm2terrn.processing.orchestrator.export_terrain_assets`.
5. The orchestrator handles heightmap/groundmap, road conversion and writing,
   OTC output, manifest TOBJ and TERRN2. Some stages can report partial
   outcomes; elevation failure has a flat-raster fallback in the current
   heightmap handler. Buildings export remains unimplemented when requested.

The street graph remains canonical in the acquisition result; an explicit
adapter constructs the `MapData` representation and road processing consumes
the same graph. Synthetic tests cover selected handoff behavior, not real
provider responses or simulator compatibility. See
[`data-handoff-analysis.md`](../book/execution/data-handoff-analysis.md).

## Distinct routes and limits

- The manual bbox choice returns an empty place label and the current CLI
  callback requires both place and bbox before downloading; see
  `osm2terrn/data/download_menu.py` and `osm2terrn/cli/commands.py`.
- `build_roads_from_place()` remains a separate compatibility route that may
  load by place; the canonical graph path is used when supplied.
- The configured Overture buildings callable is distinct from the primary
  bbox acquisition route; do not infer that it runs in every CLI export.
- A declared call path, synthetic test, generated file or static diagram does
  not establish live network availability or Rigs of Rods loading.
