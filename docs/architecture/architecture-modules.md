# Architecture: current module responsibilities

This page describes source locations present in the repository. It does not
assert that every documented design decision is fully realized. The route is
static source analysis; runtime and provider limits are in the
[execution map](../book/execution/README.md).

## Application and configuration

- `osm2terrn/app/`: application startup and session state. The declared
  application callable is `osm2terrn.app.main:main` (`pyproject.toml`,
  `[project.scripts]`; implementation in `osm2terrn/app/main.py`).
- `osm2terrn/cli/`: menu and commands (`menu.py`, `commands.py`).
- `osm2terrn/config/`: defaults, models, loading and validation.

## Data and domain

- `osm2terrn/data/`: OSM acquisition, OSMnx/Overpass integration, caching and
  layer outcomes (`osm_data_handler.py`, `overpass.py`, `acquisition.py`,
  `street_network.py`). The latter files are current untracked working-tree
  content as of 2026-11-07; inventory generation records the inspected tree.
- `osm2terrn/domain/`: entities/value objects and adapters, including conversion
  from OSMnx data to map/road domain values.

## Processing and output

- `osm2terrn/processing/terrain/`: elevation service, heightmap processing and
  terrain entrypoint generation.
- `osm2terrn/processing/network/`: road graph building/export.
- `osm2terrn/processing/roads/`: road elevation and geometry operations.
- `osm2terrn/processing/orchestrator.py`: coordinates export stages and partial
  outcomes.
- `osm2terrn/output/`: output-related current working-tree package; inspect its
  individual files before assigning broader responsibilities.
- `osm2terrn/utils/`: shared configuration-independent utilities such as
  coordinate/geometry helpers and logging.

The package's exact path inventory is generated in
[`book/inventory/files.jsonl`](../book/inventory/files.jsonl). The generator
does not replace semantic review of ownership, dynamic dispatch or behavior.
