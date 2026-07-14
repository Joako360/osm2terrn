# Architecture: change map

Use this map to find where to implement changes:

- New CLI workflow → `osm2terrn/main.py` (+ a processing module if needed).
- Download/tag filter changes → `osm2terrn/data/osm_data_handler.py`, `osm2terrn/utils/constants.py`.
- Elevation behavior changes → `osm2terrn/processing/heightmap_handler.py`.
- World size/page logic → `osm2terrn/utils/utm_utils.py`, `osm2terrn/processing/otc_exporter.py`.
- `.terrn2` fields → `osm2terrn/processing/terrn2_exporter.py`.
- Road quality/fidelity → `osm2terrn/processing/road_network_formatter.py`, `road_merger.py`, `road_exporters.py`.
