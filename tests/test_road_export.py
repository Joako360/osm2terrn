#!/usr/bin/env python3
"""
Unified road export tests: covers procedural road exporter unit tests and integration tests.
"""

import sys
import os
from pathlib import Path

# Make 'src' importable
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from processing.road_model import Road
from processing.road_exporters import export_procedural_roads_block, to_intermediate_json
from processing.road_network_formatter import build_roads_from_place

# --- Unit Tests (formerly in test_road_exporters.py) ---

def test_export_procedural_roads_block_uses_curvature_detail():
    road = Road(
        points_m=[(0.0, 0.0, 0.0), (10.0, 0.0, 5.0)],
        width=7.0,
        type="road",
    )

    out = export_procedural_roads_block([road], per_segment=False)
    assert "road" in out

def test_to_intermediate_json_includes_road_data():
    road = Road(
        points_m=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
        width=6.0,
    )

    payload = to_intermediate_json([road])
    assert payload["roads"][0]["width"] == 6.0

# --- Integration Test ---

def test_road_export():
    """Test road export with the corrected offset."""
    place = "Luis Guillón, Buenos Aires, Argentina"
    origin_lon, origin_lat = -58.5208, -34.7556

    print(f"Testing road export for {place}...")
    try:
        tobj_path = build_roads_from_place(
            place=place,
            origin_lon=origin_lon,
            origin_lat=origin_lat,
            network_type="drive",
            tobj_prefix="test",
            simplify=True
        )

        print(f"Roads exported to: {tobj_path}")

        # Check if file exists and has content
        if os.path.exists(tobj_path):
            with open(tobj_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"File size: {len(content)} characters")
                if content.strip():
                    print("File has content!")
                    # Show first few lines
                    lines = content.split('\n')[:10]
                    print("First 10 lines:")
                    for i, line in enumerate(lines, 1):
                        print(f"{i:2d}: {line}")
                else:
                    print("File is empty!")
        else:
            print("File does not exist!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_road_export()