import math
from typing import Dict, List, Tuple

from osm2terrn.processing.network.intersections.classifier import classify_intersection
from osm2terrn.processing.network.tobj_exporter import TObject

INTERSECTION_PREFABS = {
    "cross": "road-crossing",
    "tee": "road-tee",
}


def _angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _localize_point(
    point: tuple[float, float],
    to_local_fn,
    invert_y_axis: bool,
    world_offset_x: float,
    world_offset_z: float,
) -> tuple[float, float]:
    x_local, y_local = to_local_fn(point[0], point[1])
    if invert_y_axis:
        return x_local + world_offset_x, -y_local + world_offset_z
    return x_local + world_offset_x, y_local + world_offset_z


def _best_cross_rotation(angles: list[float]) -> float:
    if len(angles) != 4:
        return 0.0

    best_angle = angles[0]
    best_error = float("inf")
    for base in angles:
        targets = [(base + 90.0 * i) % 360.0 for i in range(4)]
        error = 0.0
        for angle in angles:
            closest = min(targets, key=lambda target: _angle_diff(target, angle))
            error += _angle_diff(angle, closest)
        if error < best_error:
            best_error = error
            best_angle = base
    return best_angle


def _tee_orientation_angle(angles: list[float], angle_tolerance: float = 12.0) -> float:
    if len(angles) != 3:
        return 0.0
    for i in range(3):
        for j in range(i + 1, 3):
            if _angle_diff(angles[i], angles[j]) >= 180 - angle_tolerance and _angle_diff(
                angles[i], angles[j]
            ) <= 180 + angle_tolerance:
                remaining = [angles[k] for k in range(3) if k not in {i, j}]
                return remaining[0] if remaining else 0.0
    return 0.0


def _classify_intersection_nodes(
    node_adjacency: Tuple[Dict[object, list], Dict[object, list],]) -> Dict[object, str]:
    intersection_types: Dict[object, str] = {}
    for node_id, neighbors in node_adjacency[0].items():
        degree = len(neighbors)
        if degree == 3:
            intersection_types[node_id] = "tee"
        elif degree == 4:
            intersection_types[node_id] = "cross"
        else:
            intersection_types[node_id] = "other"
    return intersection_types

def _compute_intersection_rotation(
    branch_angles: list[float],
    intersection_type: str,
    angle_tolerance: float = 12.0,
) -> float:
    if intersection_type == "cross":
        return _best_cross_rotation(branch_angles)
    if intersection_type == "tee":
        return _tee_orientation_angle(branch_angles, angle_tolerance=angle_tolerance)
    return 0.0


def _compute_average_pitch(pitches: List[float]) -> float:
    return sum(pitches) / len(pitches) if pitches else 0.0


def _compute_average_elevation(elevations: List[float]) -> float:
    return sum(elevations) / len(elevations) if elevations else 0.0


def _build_intersection_objects(
    node_types: Dict[object, str],
    adjacency: Dict[object, list],
    node_coords: Dict[object, tuple[float, float]],
    node_branch_angles: Dict[object, list],
    node_branch_pitches: Dict[object, List[float]],
    node_branch_elevations: Dict[object, List[float]],
    to_local_fn,
    invert_y_axis: bool,
    world_offset_x: float,
    world_offset_z: float,
    angle_tolerance: float = 12.0,
) -> list[TObject]:
    objects: list[TObject] = []
    for node, node_type in node_types.items():
        prefab_name = INTERSECTION_PREFABS.get(node_type)
        if prefab_name is None:
            continue
        node_coord = node_coords.get(node)
        if node_coord is None:
            continue
        branch_angles = node_branch_angles.get(node, [])
        if len(branch_angles) < 2:
            continue
        local_x, local_z = _localize_point(
            node_coord,
            to_local_fn,
            invert_y_axis,
            world_offset_x,
            world_offset_z,
        )
        yaw = _compute_intersection_rotation(branch_angles, node_type, angle_tolerance)
        pitch = _compute_average_pitch(node_branch_pitches.get(node, []))
        elevation = _compute_average_elevation(node_branch_elevations.get(node, []))
        objects.append(
            TObject(
                x=local_x,
                y=elevation,
                z=local_z,
                yaw=yaw,
                pitch=pitch,
                roll=0.0,
                obj_type=prefab_name,
                obj_file=prefab_name,
                comment=f"intersection {node_type}",
            )
        )
    return objects
