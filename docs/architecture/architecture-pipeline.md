# Architecture: pipeline overview

OSM2terrn follows a staged pipeline:

1. Input selection from CLI (`osm2terrn/main.py`).
2. OSM data acquisition (`osm2terrn/data/osm_data_handler.py`).
3. Bounds/CRS normalization (`osm2terrn/utils/bbox.py`, geometry helpers).
4. Elevation + raster generation (`osm2terrn/processing/heightmap_handler.py`).
5. Road processing (`osm2terrn/processing/road_*`).
6. RoR export writing (`.otc`, `.terrn2`, `.tobj`).
