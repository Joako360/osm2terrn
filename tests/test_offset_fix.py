#!/usr/bin/env python3
"""
Test script to verify the offset correction for Rigs of Rods coordinate system.

The Rigs of Rods coordinate system has:
- Origin (0, 0) at top-left corner
- X increases to the right
- Z increases downward
- The bottom-right corner is at (8192, 8192) for an 8192x8192 world
"""

import sys
import os
from pathlib import Path

# Make 'src' importable
ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils.geometry_utils import utm_crs_from_lonlat
from data.osm_loader import load_graph, edges_to_lines
from processing.road_merger import merge_by_highway
import geopandas as gpd
from pyproj import Transformer

def test_coordinate_transform():
    """Test the coordinate transformation with a sample place."""
    # Use hardcoded coordinates for Luis Guillón, Buenos Aires
    origin_lon, origin_lat = -58.5208, -34.7556  # WGS84 coordinates
    
    place = "Luis Guillón, Buenos Aires, Argentina"
    
    print(f"Loading graph for {place}...")
    try:
        G = load_graph(place=place, network_type="drive", simplify=True)
        geoms_attrs, src_crs = edges_to_lines(G)
        merged = merge_by_highway(geoms_attrs, merge_by_name=True)
        
        # Get the bbox - geometries from edges_to_lines are already in UTM (metric CRS)
        geoms_gdf = gpd.GeoDataFrame(
            geometry=[geom for geom, _ in merged],
            crs=src_crs  # Use the actual CRS returned from edges_to_lines
        )
        
        print(f"\nPlace origin (WGS84): {origin_lon:.6f}, {origin_lat:.6f}")
        print(f"CRS from edges: {src_crs}")
        
        # Geometries are already in UTM, just get the bounds
        minx_utm, miny_utm, maxx_utm, maxy_utm = geoms_gdf.total_bounds
        
        print(f"\nBbox in UTM:")
        print(f"  minx (west):  {minx_utm:.2f}")
        print(f"  maxy (north): {maxy_utm:.2f}")
        print(f"  maxx (east):  {maxx_utm:.2f}")
        print(f"  miny (south): {miny_utm:.2f}")
        
        # Top-left corner (0,0 in Rigs of Rods)
        x0, y0 = minx_utm, maxy_utm
        print(f"\nOrigin (top-left corner) in UTM: ({x0:.2f}, {y0:.2f})")
        
        # World size
        world_x = maxx_utm - minx_utm
        world_z = maxy_utm - miny_utm
        print(f"World size: {world_x:.2f} x {world_z:.2f} meters")
        
        # Test transformation of corner points
        print(f"\nCorner point transformation:")
        print(f"  UTM (minx, maxy) -> RoR (0, 0)")
        print(f"  UTM ({minx_utm:.2f}, {maxy_utm:.2f}) -> RoR (0, 0)")
        
        print(f"\n  UTM (maxx, miny) -> RoR ({world_x:.2f}, {world_z:.2f})")
        print(f"  UTM ({maxx_utm:.2f}, {miny_utm:.2f}) -> RoR ({world_x:.2f}, {world_z:.2f})")
        
        # Test center point
        center_x_utm = (minx_utm + maxx_utm) / 2
        center_y_utm = (miny_utm + maxy_utm) / 2
        center_x_ror = center_x_utm - x0
        center_z_ror = -(center_y_utm - y0)  # Note: Y inverted
        
        print(f"\n  UTM center ({center_x_utm:.2f}, {center_y_utm:.2f}) -> RoR ({center_x_ror:.2f}, {center_z_ror:.2f})")
        
        print("\n✅ Coordinate transformation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coordinate_transform()
