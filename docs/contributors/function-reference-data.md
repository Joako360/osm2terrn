# Function reference: data modules

## `src/data/osm_data_handler.py`
- `download_data_from_bbox(bbox)`: main OSM acquisition pipeline.
- `download_menu()`: CLI helper for place/bbox selection.
- `download_builings_from_overture(bbox)`: optional Overture building fetch.

## `src/data/osm_loader.py`
- `load_graph(place=None, bbox=None, network_type='drive')`: load OSM graph.
- `edges_to_lines(G)`: extract graph edges as line geometries + attrs.
