# Architecture: change map

Use this map to find where to implement changes:

- New CLI workflow → `src/main.py` (+ a processing module if needed).
- Download/tag filter changes → `src/data/osm_data_handler.py`, `src/utils/constants.py`.
- Elevation behavior changes → `src/processing/heightmap_handler.py`.
- World size/page logic → `src/utils/geometry_utils.py`, `src/processing/otc_exporter.py`.
- `.terrn2` fields → `src/processing/terrn2_exporter.py`.
- Road quality/fidelity → `src/processing/road_network_formatter.py`, `road_merger.py`, `road_exporters.py`.
