#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from processing.road_network_formatter import build_roads_from_place

# Set environment variables for origin
os.environ["OSM2TERRN_ORIGIN_LON"] = "-58.5300"  # Approximate longitude for Luis Guillón
os.environ["OSM2TERRN_ORIGIN_LAT"] = "-34.7500"  # Approximate latitude for Luis Guillón

place = "Luis Guillón, Buenos Aires, Argentina"
origin_lon = float(os.environ["OSM2TERRN_ORIGIN_LON"])
origin_lat = float(os.environ["OSM2TERRN_ORIGIN_LAT"])

print(f"Generating roads for {place} with origin ({origin_lon}, {origin_lat})")

try:
    roads_file = build_roads_from_place(
        place=place,
        origin_lon=origin_lon,
        origin_lat=origin_lat,
        network_type="drive",
        tobj_prefix="Luis Guillon"
    )
    print(f"Roads generated successfully: {roads_file}")
except Exception as e:
    print(f"Error generating roads: {e}")
    import traceback
    traceback.print_exc()