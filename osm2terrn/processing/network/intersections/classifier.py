"""Intersection classifier based on branch angles.

Functions here compute branch angles relative to a node and classify the
intersection type into simple categories: 'cross', 'tee', or 'other'.

All angles are returned in degrees in range [0, 360).
"""
from typing import List, Tuple
import math


def _to_deg(rad: float) -> float:
    return (math.degrees(rad) + 360.0) % 360.0


def compute_branch_angles(node_coord: Tuple[float, float], neighbor_coords: List[Tuple[float, float]]) -> List[float]:
    """Compute angles (degrees) of branches leaving `node_coord` towards each neighbor.

    neighbor_coords: list of (x, y)
    Returns a sorted list of angles in [0, 360).
    """
    cx, cy = node_coord
    angles = []
    for x, y in neighbor_coords:
        dx, dy = x - cx, y - cy
        if dx == 0 and dy == 0:
            continue
        ang = _to_deg(math.atan2(dy, dx))
        angles.append(ang)
    angles = sorted(angles)
    return angles


def _angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def classify_intersection(angles: List[float], angle_tolerance: float = 12.0) -> str:
    """Classify intersection type given sorted branch angles.

    - 'cross' if 4 branches approximately 90° apart (within tolerance)
    - 'tee' if 3 branches and two of them are approximately opposite (~180°)
    - 'other' otherwise
    """
    n = len(angles)
    if n == 4:
        # try to detect cross: find an orientation such that angles are ~[a, a+90, a+180, a+270]
        # compute differences between consecutive angles (circular)
        diffs = [ (angles[(i+1)%4] - angles[i]) % 360.0 for i in range(4) ]
        # ideal is [90,90,90,90]
        if all(_angle_diff(d, 90.0) <= angle_tolerance for d in diffs):
            return "cross"
    if n == 3:
        # find if two angles are approximately opposite
        for i in range(3):
            for j in range(i+1, 3):
                if _angle_diff(angles[i], angles[j]) >= 180 - angle_tolerance and _angle_diff(angles[i], angles[j]) <= 180 + angle_tolerance:
                    return "tee"
    return "other"
