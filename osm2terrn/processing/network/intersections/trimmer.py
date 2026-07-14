"""Road trimming helpers for intersection prefabs.

These are lightweight helpers used to compute cut points on polylines and
produce a trimmed polyline that ends at a given distance from the
intersection center. The implementation is intentionally minimal and
suitable for refinement later.
"""
from typing import List, Tuple
import math

Point = Tuple[float, float]


def _segment_length(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _interpolate(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def trim_road_to_prefab(node_coord: Point, road_coords: List[Point], cut_distance: float) -> List[Point]:
    """Trim `road_coords` starting from the node position and keep the portion
    that lies outside `cut_distance` from the node.

    road_coords: polyline ordered from node outward (first point may be node_coord).
    Returns a new polyline where the first point is located at distance `cut_distance`
    from `node_coord` along the original polyline.
    """
    if not road_coords:
        return []
    # ensure first point corresponds to node_coord (or is very near)
    pts = list(road_coords)
    # accumulate along segments until we reach cut_distance
    acc = 0.0
    for i in range(len(pts)-1):
        a, b = pts[i], pts[i+1]
        seg = _segment_length(a, b)
        if acc + seg < cut_distance:
            acc += seg
            continue
        # need to cut inside segment [a,b]
        rem = cut_distance - acc
        t = rem / seg if seg > 0 else 0.0
        cut_pt = _interpolate(a, b, t)
        # return trimmed polyline starting at cut_pt followed by remaining points
        new_pts = [cut_pt] + pts[i+1:]
        return new_pts
    # cut_distance exceeds road length; return empty (no visible road)
    return []
