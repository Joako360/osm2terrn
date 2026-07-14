"""Intersections package

Expose high-level helpers for detecting, classifying and trimming
road intersections.
"""

from .detector import detect_intersection_nodes
from .classifier import compute_branch_angles, classify_intersection
from .trimmer import trim_road_to_prefab
from .exporter import export_prefab_tobj

__all__ = [
    "detect_intersection_nodes",
    "compute_branch_angles",
    "classify_intersection",
    "trim_road_to_prefab",
    "export_prefab_tobj",
]
