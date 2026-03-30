# CLI: download flow (`dlcity`)

`dlcity()` performs the download stage:

1. Runs `download_menu()` to collect place + bbox.
2. Calls `download_data_from_bbox(bbox)`.
3. Computes origin (`lon`, `lat`) from bbox center (or centroid fallback).
4. Stores:
   - `OSM2TERRN_PLACE_NAME`
   - `OSM2TERRN_ORIGIN_LON`
   - `OSM2TERRN_ORIGIN_LAT`
5. Tries to prefetch elevation and stores it in `current_map.elevation_data`.

If input is missing or download fails, the function returns early.
