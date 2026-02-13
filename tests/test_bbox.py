import sys
import pathlib

# Ensure repository root is on sys.path so we can import src package
repo_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.utils.bbox import BBox


def test_tuple_input():
    b = BBox((0, 0, 1, 1))
    assert b.to_tuple() == (0.0, 0.0, 1.0, 1.0)
    assert b.crs is None
    assert b.is_projected is False


def test_dict_minmax_and_crs():
    data = {"minx": -1, "miny": -2, "maxx": 3, "maxy": 4, "crs": "EPSG:4326"}
    b = BBox(data)
    assert b.to_tuple() == (-1.0, -2.0, 3.0, 4.0)
    assert b.crs == "EPSG:4326"
    # EPSG:4326 should be detected as geographic
    assert b.is_projected is False


def test_object_with_total_bounds_and_projected_crs():
    class Obj:
        total_bounds = (10, 20, 30, 40)
        crs = "EPSG:3857"

    b = BBox(Obj())
    assert b.to_tuple() == (10.0, 20.0, 30.0, 40.0)
    assert b.crs == "EPSG:3857"
    # Heuristic should mark 3857 as projected even if pyproj isn't installed
    assert b.is_projected is True
