import math
import numpy as np
from typing import List, Optional, Tuple

from shapely.geometry import LineString


def trim_distance_for_degree(degree: int) -> float:
    """Return endpoint trim distance (meters) based on intersection complexity."""
    if degree >= 5:
        return 10.0
    if degree == 4:
        return 8.0
    if degree == 3:
        return 6.0
    return 0.0


def trim_linestring_between_intersections(
    line: LineString,
    start_degree: int,
    end_degree: int,
) -> Optional[LineString]:
    """
    Trim both ends of a linestring so roads do not overlap through intersection centers.
    Returns None when the trimmed geometry becomes too short.
    """
    total = float(line.length)
    if total <= 0.01:
        return None

    start_trim = trim_distance_for_degree(start_degree)
    end_trim = trim_distance_for_degree(end_degree)
    max_trim = total * 0.45
    start_trim = min(start_trim, max_trim)
    end_trim = min(end_trim, max_trim)

    start_d = start_trim
    end_d = total - end_trim
    if end_d - start_d < 2.0:
        return None

    p0 = line.interpolate(start_d)
    p1 = line.interpolate(end_d)
    coords = [(p0.x, p0.y)] + list(line.coords)[1:-1] + [(p1.x, p1.y)]
    cleaned: List[Tuple[float, ...]] = []
    for coord in coords:
        if not cleaned or coord != cleaned[-1]:
            cleaned.append(coord)
    if len(cleaned) < 2:
        return None
    trimmed = LineString(cleaned)
    return trimmed if trimmed.length >= 2.0 else None


def to_local_xz(
    line: LineString,
    to_local_fn,
    invert_y_axis: bool = True,
    world_offset_x: float = 0.0,
    world_offset_z: float = 0.0,
) -> List[Tuple[float, float]]:
    """Transform a linestring into local XZ coordinates using a local CRS."""
    from shapely.ops import transform as shp_transform

    line_local = shp_transform(to_local_fn, line)
    x_coords, y_coords = line_local.xy

    local_xy: List[Tuple[float, float]] = [(float(x), float(y)) for x, y in zip(x_coords, y_coords)]

    if invert_y_axis:
        return [(float(lx + world_offset_x), float(-ly + world_offset_z)) for lx, ly in local_xy]
    return [(float(lx + world_offset_x), float(ly + world_offset_z)) for lx, ly in local_xy]


def normalize_heading_to_ror(yaw_deg: float) -> float:
    """Normalize a heading yaw for the RoR rotation convention."""
    normalized = yaw_deg % 360.0
    return float(normalized if normalized >= 0.0 else normalized + 360.0)


def compute_heading_pitch(
    dx: float,
    dz: float,
    dy: float = 0.0,
) -> tuple[float, float]:
    """Compute RoR yaw and pitch from a direction vector in local XZ space."""
    if dx == 0.0 and dz == 0.0:
        return 0.0, 0.0

    yaw_deg = normalize_heading_to_ror(math.degrees(math.atan2(dz, dx)))
    horiz_len = math.hypot(dx, dz)
    pitch_deg = math.degrees(math.atan2(dy, horiz_len)) if horiz_len > 1e-6 else 0.0
    return float(yaw_deg), float(pitch_deg)


def build_oriented_points(
    local_xz: List[Tuple[float, float]],
    sampled_z: "np.ndarray",
) -> Tuple[List[tuple], List[float], List[float]]:
    """Build 3D points and per-point yaw/pitch values along a segment."""
    local_pts_m: List[tuple] = []
    yaw_list: List[float] = []
    pitch_list: List[float] = []

    for i, (px, pz) in enumerate(local_xz):
        py = float(sampled_z[i])
        if i < len(local_xz) - 1:
            dx = local_xz[i + 1][0] - px
            dz = local_xz[i + 1][1] - pz
            dy = float(sampled_z[i + 1] - sampled_z[i])
        elif i > 0:
            dx = px - local_xz[i - 1][0]
            dz = pz - local_xz[i - 1][1]
            dy = float(sampled_z[i] - sampled_z[i - 1])
        else:
            dx = dz = dy = 0.0

        yaw_deg, pitch_deg = compute_heading_pitch(dx, dz, dy)
        yaw_list.append(yaw_deg)
        pitch_list.append(pitch_deg)
        local_pts_m.append((float(px), float(py), float(pz)))

    return local_pts_m, yaw_list, pitch_list
