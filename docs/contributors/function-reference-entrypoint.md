# Function reference: entry point and session flow

## `src/main.py`
- `MapData`: session container for `data` and `elevation_data`.
- `dlcity()`: download menu + OSM fetch + origin env setup + elevation prefetch.
- `load()`: placeholder import/cached-load stage.
- `export()`: raster generation + optional road export + `.otc/.terrn2/.tobj` output.
- `Menu`: text UI (`show`, `run`).
