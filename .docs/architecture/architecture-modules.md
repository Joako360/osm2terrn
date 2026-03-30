# Architecture: module responsibilities

## `src/data`
- `osm_data_handler.py`: download orchestration and bbox/place handling.
- `osm_loader.py`: graph loading and graph-to-lines conversion.

## `src/processing`
- `heightmap_handler.py`: elevation retrieval and raster generation.
- `road_network_formatter.py`: end-to-end road pipeline.
- `road_merger.py` and `road_exporters.py`: road merge/serialization utilities.
- `otc_exporter.py`, `terrn2_exporter.py`, `tobj_exporter.py`: output writers.

## `src/utils`
- `bbox.py`: canonical bbox representation.
- `geometry.py`, `geometry_utils.py`: transform/world-size helpers.
- `constants.py`: global defaults.
- `logger.py`: logging helpers.
