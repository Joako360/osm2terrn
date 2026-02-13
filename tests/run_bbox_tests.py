import sys
import pathlib

# Ensure repository root is on sys.path so we can import src package
repo_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
# Also make the package-level imports like `utils` resolvable by adding src/ to path
sys.path.insert(0, str(repo_root / "src"))

from src.utils.bbox import BBox


def run():
    failures = []

    try:
        b = BBox((0, 0, 1, 1))
        assert b.to_tuple() == (0.0, 0.0, 1.0, 1.0)
        assert b.crs is None
        assert b.is_projected is False
    except Exception as e:
        failures.append(f"test_tuple_input failed: {e}")

    try:
        data = {"minx": -1, "miny": -2, "maxx": 3, "maxy": 4, "crs": "EPSG:4326"}
        b = BBox(data)
        assert b.to_tuple() == (-1.0, -2.0, 3.0, 4.0)
        assert b.crs == "EPSG:4326"
        assert b.is_projected is False
    except Exception as e:
        failures.append(f"test_dict_minmax_and_crs failed: {e}")

    try:
        class Obj:
            total_bounds = (10, 20, 30, 40)
            crs = "EPSG:3857"

        b = BBox(Obj())
        assert b.to_tuple() == (10.0, 20.0, 30.0, 40.0)
        assert b.crs == "EPSG:3857"
        assert b.is_projected is True
    except Exception as e:
        failures.append(f"test_object_with_total_bounds_and_projected_crs failed: {e}")

    if failures:
        print("FAILURES:\n" + "\n".join(failures))
        raise SystemExit(1)
    else:
        print("All bbox tests passed")


if __name__ == "__main__":
    run()
