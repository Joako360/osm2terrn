import math
from osm2terrn.processing.network.intersections.classifier import (
    compute_branch_angles,
    classify_intersection,
)


def test_perfect_cross():
    node = (0.0, 0.0)
    neighbors = [ (1,0), (0,1), (-1,0), (0,-1) ]
    angles = compute_branch_angles(node, neighbors)
    assert len(angles) == 4
    assert classify_intersection(angles, angle_tolerance=5.0) == "cross"


def test_perfect_tee():
    node = (0.0, 0.0)
    neighbors = [ (1,0), (-1,0), (0,1) ]
    angles = compute_branch_angles(node, neighbors)
    assert len(angles) == 3
    assert classify_intersection(angles, angle_tolerance=5.0) == "tee"


def test_other():
    node = (0.0, 0.0)
    neighbors = [ (1,0), (0.5,0.2), (-0.2,1.0) ]
    angles = compute_branch_angles(node, neighbors)
    assert classify_intersection(angles) == "other"
