# CLI: export flow (`export`)

This is a static map of `osm2terrn.cli.commands.export` and
`osm2terrn.processing.orchestrator.export_terrain_assets`. It does not claim a
complete interactive run or Rigs of Rods compatibility.

1. The callback checks that session map data exists and passes its bounds,
   elevation data, place/origin, canonical `StreetNetworkResult`, acquisition
   outcomes and target terrain size to the orchestrator.
2. The orchestrator assembles `MapData`, converting the canonical graph through
   the explicit adapter when roads are requested and available. It does not
   reload that graph by place on this route.
3. `export.include_roads` gates the road path. A successful empty network,
   missing network and failed acquisition have distinct statuses and reporting.
4. Heightmap processing can use supplied elevation or fetch through its
   service/cache path; source includes a flat-raster fallback on fetch failure.
5. The orchestrator writes terrain raster/OTC/TOBJ/TERRN2 outputs and reports
   partial outcomes. Requested buildings export is currently reported as not
   implemented.

The streets handoff has synthetic-test evidence only. Real provider payloads,
DEM alignment and simulator loading remain unverified. See the
[detailed execution map](../book/execution/README.md) and
[handoff analysis](../book/execution/data-handoff-analysis.md).
