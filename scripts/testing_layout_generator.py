import argparse
import json
import math
import sys
from pathlib import Path
from typing import Callable, Optional, TypeVar

import numpy as np

# Ensure the project source directory is importable when running this script directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from processing.road_geometry import build_oriented_points
from processing.road_model import Road
from processing.tobj_exporter import TobjExporter
from processing.road_exporters import to_intermediate_json


def bezier_curve(P0, P1, P2, P3, n=50):
    """Generate a cubic Bezier polyline from four control points.

    Args:
        P0: The first control point as a 2D or 3D tuple.
        P1: The second control point as a 2D or 3D tuple.
        P2: The third control point as a 2D or 3D tuple.
        P3: The fourth control point as a 2D or 3D tuple.
        n: Number of points to sample along the curve.

    Returns:
        A list of 2D or 3D points representing the Bezier curve.
    """
    P0 = np.array(P0, dtype=float)
    P1 = np.array(P1, dtype=float)
    P2 = np.array(P2, dtype=float)
    P3 = np.array(P3, dtype=float)

    curve = []
    for t in np.linspace(0, 1, n):
        p = (
            ((1 - t) ** 3) * P0
            + 3 * ((1 - t) ** 2) * t * P1
            + 3 * (1 - t) * (t ** 2) * P2
            + (t ** 3) * P3
        )
        curve.append(tuple(p))
    return curve


def offset_polyline(points, offset):
    """Offset a polyline by a fixed distance to create a parallel curve.

    Args:
        points: List of 2D points defining the source polyline.
        offset: Distance to offset the polyline, positive to the left of travel.

    Returns:
        A new list of 2D points representing the offset polyline.
    """
    result = []
    normal = np.array([0.0, 0.0])

    for i in range(len(points) - 1):
        p1 = np.array(points[i], dtype=float)
        p2 = np.array(points[i + 1], dtype=float)
        direction = p2 - p1
        direction = direction / np.linalg.norm(direction)
        normal = np.array([-direction[1], direction[0]])
        result.append(tuple(p1 + normal * offset))

    result.append(tuple(np.array(points[-1], dtype=float) + normal * offset))
    return result


def make_road(points, width=8.0, road_type="road", name=None, border_width=0.5, border_height=0.2):
    """Build a Road object from a list of 2D/3D coordinates.

    Args:
        points: List of points in 2D or 3D space. 2D points are interpreted as (x, z).
        width: Road surface width in meters.
        road_type: Procedural road type used for .tobj export.
        name: Optional name for the road segment.
        border_width: Border width for procedural road rendering.
        border_height: Border height for procedural road rendering.

    Returns:
        A Road instance ready for export.
    """
    local_xz = []
    sampled_z = []

    for point in points:
        if len(point) == 2:
            x, z = point
            local_xz.append((float(x), float(z)))
            sampled_z.append(0.0)
        elif len(point) == 3:
            local_xz.append((float(point[0]), float(point[2])))
            sampled_z.append(float(point[1]))
        else:
            raise ValueError("Each point must be a 2D or 3D tuple")

    points_m, yaw_deg, pitch_deg = build_oriented_points(local_xz, np.array(sampled_z, dtype=float))

    return Road(
        points_m=points_m,
        width=float(width),
        border_width=float(border_width),
        border_height=float(border_height),
        type=road_type,
        name=name,
        yaw_deg=yaw_deg,
        pitch_deg=pitch_deg,
    )


def build_grid(rows=5, cols=5, spacing=100.0, width=8.0, border_width=0.5, border_height=0.2):
    """Create a grid of straight road segments.

    Args:
        rows: Number of horizontal row lines.
        cols: Number of vertical column lines.
        spacing: Distance between each grid point in meters.
        width: Road width for each segment.
        border_width: Road border width.
        border_height: Road border height.

    Returns:
        A list of Road objects forming a rectangular grid.
    """
    roads = []
    for i in range(rows):
        for j in range(cols - 1):
            p1 = (j * spacing, i * spacing)
            p2 = ((j + 1) * spacing, i * spacing)
            roads.append(
                make_road(
                    [p1, p2],
                    width=width,
                    road_type="road",
                    name=f"grid_row_{i}_{j}",
                    border_width=border_width,
                    border_height=border_height,
                )
            )

    for j in range(cols):
        for i in range(rows - 1):
            p1 = (j * spacing, i * spacing)
            p2 = (j * spacing, (i + 1) * spacing)
            roads.append(
                make_road(
                    [p1, p2],
                    width=width,
                    road_type="road",
                    name=f"grid_col_{j}_{i}",
                    border_width=border_width,
                    border_height=border_height,
                )
            )
    return roads


def build_roundabout(center_x=0.0, center_y=0.0, radius_x=30.0, radius_y=None, segments=24, width=8.0, border_width=0.5, border_height=0.2):
    """Create a circular roundabout as a continuous road loop.

    Args:
        center_x: X coordinate for the roundabout center.
        center_y: Z coordinate for the roundabout center.
        radius_x: Radius in the X direction.
        radius_y: Radius in the Z direction. If None, uses radius_x.
        segments: Number of sample points for the curve.
        width: Road width.
        border_width: Road border width.
        border_height: Road border height.

    Returns:
        A list containing a single Road object representing the roundabout.
    """
    if radius_y is None:
        radius_y = radius_x

    points = []
    for i in range(segments + 1):
        theta = 2 * math.pi * i / segments
        x = center_x + radius_x * math.cos(theta)
        y = center_y + radius_y * math.sin(theta)
        points.append((x, y))

    return [
        make_road(
            points,
            width=width,
            road_type="roundabout",
            name="roundabout",
            border_width=border_width,
            border_height=border_height,
        )
    ]


def build_curve(P0, P1, P2, P3, segments=50, width=8.0, border_width=0.5, border_height=0.2):
    """Create a single curved road from cubic Bezier control points.

    Args:
        P0: Start control point as (x, z).
        P1: First handle control point as (x, z).
        P2: Second handle control point as (x, z).
        P3: End control point as (x, z).
        segments: Number of points sampled on the curve.
        width: Road width.
        border_width: Road border width.
        border_height: Road border height.

    Returns:
        A list containing a single Road object for the curve.
    """
    curve = bezier_curve(P0, P1, P2, P3, n=segments)
    return [
        make_road(
            curve,
            width=width,
            road_type="road",
            name="curved_road",
            border_width=border_width,
            border_height=border_height,
        )
    ]


def build_dual_carriageway(P0, P1, P2, P3, offset=10.0, segments=50, width=8.0, border_width=0.5, border_height=0.2):
    """Build a dual carriageway using an offset Bezier centerline.

    Args:
        P0: Start control point as (x, z).
        P1: First handle control point as (x, z).
        P2: Second handle control point as (x, z).
        P3: End control point as (x, z).
        offset: Separation distance between opposing carriageways.
        segments: Number of sample points along the centerline.
        width: Road width for each side.
        border_width: Road border width.
        border_height: Road border height.

    Returns:
        A list of two Road objects representing both carriageways.
    """
    centerline = bezier_curve(P0, P1, P2, P3, n=segments)
    side_a = offset_polyline(centerline, offset)
    side_b = offset_polyline(centerline, -offset)

    return [
        make_road(
            side_a,
            width=width,
            road_type="highway",
            name="dual_carriageway_side_a",
            border_width=border_width,
            border_height=border_height,
        ),
        make_road(
            side_b,
            width=width,
            road_type="highway",
            name="dual_carriageway_side_b",
            border_width=border_width,
            border_height=border_height,
        ),
    ]


def create_periodic_plazas(rows, cols, interval=6, size=2):
    """Generate periodic plaza cell definitions for a grid.

    Args:
        rows: Number of grid rows.
        cols: Number of grid columns.
        interval: Distance between plaza centers in grid cells.
        size: Square radius around each plaza center.

    Returns:
        A list of plaza dictionaries with row, col, and size.
    """
    plazas = []
    for i in range(interval // 2, rows, interval):
        for j in range(interval // 2, cols, interval):
            plazas.append({"row": i, "col": j, "size": size})
    return plazas


def add_central_square(plazas, rows, cols, size=4):
    """Add a central plaza to the existing plaza list."""
    plazas.append({"row": rows // 2, "col": cols // 2, "size": size})
    return plazas


def is_plaza_cell(r, c, plazas):
    """Return True if the given cell falls inside any plaza area."""
    for plaza in plazas:
        if abs(r - plaza["row"]) < plaza["size"] and abs(c - plaza["col"]) < plaza["size"]:
            return True
    return False


def build_smart_grid(rows=30, cols=30, spacing=100.0, interval=6, plaza_size=2, central_square=True, width=8.0, border_width=0.5, border_height=0.2):
    """Create a smart grid with periodic plazas and optional central square.

    Args:
        rows: Number of grid rows.
        cols: Number of grid columns.
        spacing: Distance between grid points in meters.
        interval: Interval for periodic plazas.
        plaza_size: Plaza half-size in cell units.
        central_square: Whether to include a central plaza.
        width: Road width for each grid segment.
        border_width: Road border width.
        border_height: Road border height.

    Returns:
        A list of Road objects representing the smart grid.
    """
    plazas = create_periodic_plazas(rows, cols, interval=interval, size=plaza_size)
    if central_square:
        plazas = add_central_square(plazas, rows, cols, size=plaza_size)

    roads = []
    valid_cells = {
        (i, j)
        for i in range(rows)
        for j in range(cols)
        if not is_plaza_cell(i, j, plazas)
    }

    for i, j in valid_cells:
        if j + 1 < cols and (i, j + 1) in valid_cells:
            p1 = (j * spacing, i * spacing)
            p2 = ((j + 1) * spacing, i * spacing)
            roads.append(
                make_road(
                    [p1, p2],
                    width=width,
                    road_type="street",
                    name=f"smart_grid_row_{i}_{j}",
                    border_width=border_width,
                    border_height=border_height,
                )
            )
        if i + 1 < rows and (i + 1, j) in valid_cells:
            p1 = (j * spacing, i * spacing)
            p2 = (j * spacing, (i + 1) * spacing)
            roads.append(
                make_road(
                    [p1, p2],
                    width=width,
                    road_type="street",
                    name=f"smart_grid_col_{j}_{i}",
                    border_width=border_width,
                    border_height=border_height,
                )
            )
    return roads


def add_major_avenues(rows, cols, spacing=100.0, interval=6, width=20.0, border_width=0.5, border_height=0.2):
    """Create major avenue road segments at regular intervals."""
    roads = []
    for i in range(0, rows, interval):
        for j in range(cols - 1):
            p1 = (j * spacing, i * spacing)
            p2 = ((j + 1) * spacing, i * spacing)
            roads.append(
                make_road(
                    [p1, p2],
                    width=width,
                    road_type="avenue",
                    name=f"avenue_row_{i}_{j}",
                    border_width=border_width,
                    border_height=border_height,
                )
            )
    return roads


def add_main_diagonals(rows, cols, spacing=100.0, width=25.0, border_width=0.5, border_height=0.2):
    """Create diagonal roads through the grid."""
    roads = []
    n = min(rows, cols)
    for i in range(n - 1):
        p1 = (i * spacing, i * spacing)
        p2 = ((i + 1) * spacing, (i + 1) * spacing)
        roads.append(
            make_road(
                [p1, p2],
                width=width,
                road_type="diagonal",
                name=f"main_diagonal_{i}",
                border_width=border_width,
                border_height=border_height,
            )
        )
    return roads


def add_ring_avenue(rows, cols, spacing=100.0, width=25.0, border_width=0.5, border_height=0.2):
    """Create a ring avenue around the perimeter of the grid."""
    points = [
        (0.0, 0.0),
        (cols * spacing, 0.0),
        (cols * spacing, rows * spacing),
        (0.0, rows * spacing),
        (0.0, 0.0),
    ]
    return [
        make_road(
            points,
            width=width,
            road_type="ring",
            name="ring_avenue",
            border_width=border_width,
            border_height=border_height,
        )
    ]


def build_city_layout(rows=40, cols=40, spacing=120.0, interval=6, plaza_size=2, width=8.0, avenue_width=20.0, diagonal_width=25.0):
    """Create a city-like layout combining smart grid, plazas, avenues, diagonals and a ring.

    Returns:
        A list of Road objects representing a larger sample city layout.
    """
    roads = []
    roads.extend(build_smart_grid(rows=rows, cols=cols, spacing=spacing, interval=interval, plaza_size=plaza_size, central_square=True, width=width))
    roads.extend(add_major_avenues(rows=rows, cols=cols, spacing=spacing, interval=interval, width=avenue_width))
    roads.extend(add_main_diagonals(rows=rows, cols=cols, spacing=spacing, width=diagonal_width))
    roads.extend(add_ring_avenue(rows=rows, cols=cols, spacing=spacing, width=diagonal_width))
    return roads


def build_combo():
    """Create a combined sample set for grid, roundabout, curve, and dual highway.

    Returns:
        A list of Road objects that demonstrates multiple export cases.
    """
    roads = []
    roads.extend(build_grid(rows=5, cols=5, spacing=120.0, width=8.0))
    roads.extend(build_roundabout(center_x=240.0, center_y=240.0, radius_x=40.0, radius_y=30.0, segments=36, width=10.0))
    roads.extend(build_curve((0.0, 600.0), (200.0, 520.0), (400.0, 700.0), (600.0, 640.0), segments=80, width=10.0))
    roads.extend(build_dual_carriageway((0.0, 900.0), (200.0, 820.0), (400.0, 980.0), (600.0, 900.0), offset=15.0, segments=80, width=8.0))
    return roads


def save_roads(roads, output_dir, filename):
    """Export a list of roads to a .tobj file and save debug JSON.

    Args:
        roads: List of Road objects to export.
        output_dir: Directory path where outputs will be saved.
        filename: Name of the .tobj file.
    """
    exporter = TobjExporter(output_dir=str(output_dir))
    exporter.export_to_tobj(roads=roads, filename=filename, include_procedural_roads=True)
    json_path = output_dir / f"{Path(filename).stem}_roads.json"
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(to_intermediate_json(roads), handle, indent=2)
    print(f"Generated {len(roads)} roads")
    print(f"Saved .tobj to: {output_dir / filename}")
    print(f"Saved debug JSON to: {json_path}")


def parse_point_list(value):
    """Parse a comma-separated list of floats into a point coordinate sequence.

    Args:
        value: Comma-separated numeric values.

    Returns:
        A list of floats parsed from the string.

    Raises:
        argparse.ArgumentTypeError: If the value does not contain the expected number of floats.
    """
    floats = [float(item) for item in value.split(",")]
    if len(floats) not in (8, 12):
        raise argparse.ArgumentTypeError("Point list must contain 8 or 12 floats")
    return floats


T = TypeVar("T")

def prompt_value(prompt: str, default: Optional[T] = None, cast: Callable[[str], T] = str) -> Optional[T]:
    """Prompt the user for a value and return the typed result.

    Args:
        prompt: Prompt text to display.
        default: Default value if the user presses Enter.
        cast: Callable to convert the input string.

    Returns:
        The converted input value, or the default.
    """
    while True:
        default_display = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{default_display}: ").strip()
        if raw == "":
            return default
        try:
            return cast(raw)
        except ValueError:
            cast_name = getattr(cast, "__name__", type(cast).__name__)
            print(f"Invalid value for {prompt}. Please enter a valid {cast_name}.")


def prompt_points(prompt, default=None):
    """Prompt the user for a comma-separated point list.

    Args:
        prompt: Prompt text to display.
        default: Default comma-separated point string.

    Returns:
        A list of floats parsed from the user input.
    """
    while True:
        default_display = f" [{default}]" if default else ""
        raw = input(f"{prompt}{default_display}: ").strip()
        if raw == "" and default is not None:
            raw = default
        try:
            return parse_point_list(raw)
        except argparse.ArgumentTypeError as exc:
            print(exc)


def run_interactive():
    """Run an interactive prompt session to build road example parameters.

    Returns:
        An argparse.Namespace containing the selected command and its parameters.
    """
    print("Interactive road generator")
    commands = ["grid", "roundabout", "curve", "dual-carriageway", "combo"]
    for index, command in enumerate(commands, start=1):
        print(f"{index}. {command}")

    choice = prompt_value("Choose an option by number", default=1, cast=int)
    if choice < 1 or choice > len(commands):#type: ignore
        raise ValueError("Invalid selection")

    command = commands[choice - 1]#type: ignore
    args = argparse.Namespace(command=command)

    if command == "grid":
        args.rows = prompt_value("Rows", default=5, cast=int)
        args.cols = prompt_value("Cols", default=5, cast=int)
        args.spacing = prompt_value("Spacing", default=100.0, cast=float)
        args.width = prompt_value("Road width", default=8.0, cast=float)
        args.border_width = prompt_value("Border width", default=0.5, cast=float)
        args.border_height = prompt_value("Border height", default=0.2, cast=float)
        args.filename = prompt_value("Filename", default="grid_roads.tobj", cast=str)
    elif command == "roundabout":
        args.center_x = prompt_value("Center X", default=0.0, cast=float)
        args.center_y = prompt_value("Center Y", default=0.0, cast=float)
        args.radius_x = prompt_value("Radius X", default=30.0, cast=float)
        args.radius_y = prompt_value("Radius Y", default=None, cast=lambda v: float(v) if v != "" else None)
        args.segments = prompt_value("Segments", default=24, cast=int)
        args.width = prompt_value("Road width", default=8.0, cast=float)
        args.border_width = prompt_value("Border width", default=0.5, cast=float)
        args.border_height = prompt_value("Border height", default=0.2, cast=float)
        args.filename = prompt_value("Filename", default="roundabout_roads.tobj", cast=str)
    elif command == "curve":
        args.points = prompt_points(
            "Control points (x0,z0,x1,z1,x2,z2,x3,z3)",
            default="0,0,100,0,200,100,300,100",
        )
        args.segments = prompt_value("Segments", default=50, cast=int)
        args.width = prompt_value("Road width", default=8.0, cast=float)
        args.border_width = prompt_value("Border width", default=0.5, cast=float)
        args.border_height = prompt_value("Border height", default=0.2, cast=float)
        args.filename = prompt_value("Filename", default="curved_roads.tobj", cast=str)
    elif command == "dual-carriageway":
        args.points = prompt_points(
            "Control points (x0,z0,x1,z1,x2,z2,x3,z3)",
            default="0,0,100,0,200,100,300,100",
        )
        args.offset = prompt_value("Offset", default=10.0, cast=float)
        args.segments = prompt_value("Segments", default=50, cast=int)
        args.width = prompt_value("Road width", default=8.0, cast=float)
        args.border_width = prompt_value("Border width", default=0.5, cast=float)
        args.border_height = prompt_value("Border height", default=0.2, cast=float)
        args.filename = prompt_value("Filename", default="dual_carriageway_roads.tobj", cast=str)
    elif command == "combo":
        args.filename = prompt_value("Filename", default="combo_roads.tobj", cast=str)
    else:
        raise ValueError("Unsupported interactive command")

    args.output_dir = prompt_value("Output directory", default="output/road_examples", cast=str)
    return args


def main():
    """Parse CLI arguments and execute the requested road generation flow.

    Supports both non-interactive subcommands and an interactive prompt mode.
    """
    parser = argparse.ArgumentParser(
        description="Generate example roads for Rigs of Rods export testing."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    grid_parser = subparsers.add_parser("grid", help="Generate an n x m grid of straight roads")
    grid_parser.add_argument("--rows", type=int, default=5)
    grid_parser.add_argument("--cols", type=int, default=5)
    grid_parser.add_argument("--spacing", type=float, default=100.0)
    grid_parser.add_argument("--width", type=float, default=8.0)
    grid_parser.add_argument("--border-width", type=float, default=0.5)
    grid_parser.add_argument("--border-height", type=float, default=0.2)
    grid_parser.add_argument("--filename", default="grid_roads.tobj")
    grid_parser.add_argument("--output-dir", default="output/road_examples")

    roundabout_parser = subparsers.add_parser("roundabout", help="Generate a roundabout road example")
    roundabout_parser.add_argument("--center-x", type=float, default=0.0)
    roundabout_parser.add_argument("--center-y", type=float, default=0.0)
    roundabout_parser.add_argument("--radius-x", type=float, default=30.0)
    roundabout_parser.add_argument("--radius-y", type=float)
    roundabout_parser.add_argument("--segments", type=int, default=24)
    roundabout_parser.add_argument("--width", type=float, default=8.0)
    roundabout_parser.add_argument("--border-width", type=float, default=0.5)
    roundabout_parser.add_argument("--border-height", type=float, default=0.2)
    roundabout_parser.add_argument("--filename", default="roundabout_roads.tobj")
    roundabout_parser.add_argument("--output-dir", default="output/road_examples")

    curve_parser = subparsers.add_parser("curve", help="Generate a curved road using cubic Bezier control points")
    curve_parser.add_argument("--points", type=parse_point_list, required=True,
                              help="Comma-separated coordinates for P0,P1,P2,P3 as x0,z0,x1,z1,x2,z2,x3,z3")
    curve_parser.add_argument("--segments", type=int, default=50)
    curve_parser.add_argument("--width", type=float, default=8.0)
    curve_parser.add_argument("--border-width", type=float, default=0.5)
    curve_parser.add_argument("--border-height", type=float, default=0.2)
    curve_parser.add_argument("--filename", default="curved_roads.tobj")
    curve_parser.add_argument("--output-dir", default="output/road_examples")

    dual_parser = subparsers.add_parser("dual-carriageway", help="Generate a dual carriageway from a Bezier centerline")
    dual_parser.add_argument("--points", type=parse_point_list, required=True,
                             help="Comma-separated coordinates for P0,P1,P2,P3 as x0,z0,x1,z1,x2,z2,x3,z3")
    dual_parser.add_argument("--offset", type=float, default=10.0)
    dual_parser.add_argument("--segments", type=int, default=50)
    dual_parser.add_argument("--width", type=float, default=8.0)
    dual_parser.add_argument("--border-width", type=float, default=0.5)
    dual_parser.add_argument("--border-height", type=float, default=0.2)
    dual_parser.add_argument("--filename", default="dual_carriageway_roads.tobj")
    dual_parser.add_argument("--output-dir", default="output/road_examples")

    city_parser = subparsers.add_parser("city", help="Generate a city layout with plazas, avenues, diagonals, and ring road")
    city_parser.add_argument("--rows", type=int, default=40)
    city_parser.add_argument("--cols", type=int, default=40)
    city_parser.add_argument("--spacing", type=float, default=120.0)
    city_parser.add_argument("--interval", type=int, default=6)
    city_parser.add_argument("--plaza-size", type=int, default=2)
    city_parser.add_argument("--width", type=float, default=8.0)
    city_parser.add_argument("--avenue-width", type=float, default=20.0)
    city_parser.add_argument("--diagonal-width", type=float, default=25.0)
    city_parser.add_argument("--filename", default="city_layout_roads.tobj")
    city_parser.add_argument("--output-dir", default="output/road_examples")

    combo_parser = subparsers.add_parser("combo", help="Generate a combined example with grid, roundabout, curve, and dual carriageway")
    combo_parser.add_argument("--filename", default="combo_roads.tobj")
    combo_parser.add_argument("--output-dir", default="output/road_examples")

    subparsers.add_parser("interactive", help="Run interactive CLI prompts to generate a road example")

    parser.add_argument("--output-dir", default="output/road_examples")

    args = parser.parse_args()
    if args.command == "interactive":
        args = run_interactive()

    output_dir = Path(getattr(args, 'output_dir', 'output/road_examples'))
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.command == "grid":
        roads = build_grid(
            rows=args.rows,
            cols=args.cols,
            spacing=args.spacing,
            width=args.width,
            border_width=args.border_width,
            border_height=args.border_height,
        )
    elif args.command == "roundabout":
        roads = build_roundabout(
            center_x=args.center_x,
            center_y=args.center_y,
            radius_x=args.radius_x,
            radius_y=args.radius_y,
            segments=args.segments,
            width=args.width,
            border_width=args.border_width,
            border_height=args.border_height,
        )
    elif args.command == "curve":
        px = args.points
        roads = build_curve(
            (px[0], px[1]),
            (px[2], px[3]),
            (px[4], px[5]),
            (px[6], px[7]),
            segments=args.segments,
            width=args.width,
            border_width=args.border_width,
            border_height=args.border_height,
        )
    elif args.command == "dual-carriageway":
        px = args.points
        roads = build_dual_carriageway(
            (px[0], px[1]),
            (px[2], px[3]),
            (px[4], px[5]),
            (px[6], px[7]),
            offset=args.offset,
            segments=args.segments,
            width=args.width,
            border_width=args.border_width,
            border_height=args.border_height,
        )
    elif args.command == "city":
        roads = build_city_layout(
            rows=args.rows,
            cols=args.cols,
            spacing=args.spacing,
            interval=args.interval,
            plaza_size=args.plaza_size,
            width=args.width,
            avenue_width=args.avenue_width,
            diagonal_width=args.diagonal_width,
        )
    elif args.command == "combo":
        roads = build_combo()
    else:
        raise ValueError(f"Unknown command: {args.command}")

    save_roads(roads, output_dir, args.filename)


if __name__ == "__main__":
    main()
