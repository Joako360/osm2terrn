# Architecture: pipeline overview

OSM2terrn follows a staged pipeline:

1. Input selection from CLI (`src/main.py`).
2. OSM data acquisition (`src/data/osm_data_handler.py`).
3. Bounds/CRS normalization (`src/utils/bbox.py`, geometry helpers).
4. Elevation + raster generation (`src/processing/heightmap_handler.py`).
5. Road processing (`src/processing/road_*`).
6. RoR export writing (`.otc`, `.terrn2`, `.tobj`).
