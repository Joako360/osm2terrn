from shapely.geometry import LineString

from osm2terrn.processing.network.road_network_graph_build import (
    _build_node_graph,
)
from osm2terrn.processing.network.road_network_graph_intersections import (
    _best_cross_rotation,
    _build_intersection_objects,
    _classify_intersection_nodes,
    _tee_orientation_angle,
)


def test_classify_synthetic_cross_intersection():
    # Four road segments connected at a central node, forming a perfect cross.
    merged_dense = [
        (LineString([(0.0, 0.0), (10.0, 0.0)]), {"u": 0, "v": 1}),
        (LineString([(0.0, 0.0), (0.0, 10.0)]), {"u": 0, "v": 2}),
        (LineString([(0.0, 0.0), (-10.0, 0.0)]), {"u": 0, "v": 3}),
        (LineString([(0.0, 0.0), (0.0, -10.0)]), {"u": 0, "v": 4}),
    ]

    node_degree, node_adjacency, node_coords, node_branch_angles = _build_node_graph(merged_dense)
    node_types = _classify_intersection_nodes((node_adjacency, node_branch_angles))

    assert node_degree[0] == 4
    assert node_types[0] == "cross"


def test_classify_synthetic_tee_intersection():
    # Three road segments connected at a central node, forming a T intersection.
    merged_dense = [
        (LineString([(0.0, 0.0), (10.0, 0.0)]), {"u": 0, "v": 1}),
        (LineString([(0.0, 0.0), (-10.0, 0.0)]), {"u": 0, "v": 2}),
        (LineString([(0.0, 0.0), (0.0, 10.0)]), {"u": 0, "v": 3}),
    ]

    node_degree, node_adjacency, node_coords, node_branch_angles = _build_node_graph(merged_dense)
    node_types = _classify_intersection_nodes((node_adjacency, node_branch_angles))

    assert node_degree[0] == 3
    assert node_types[0] == "tee"


def test_build_intersection_objects_for_cross():
    merged_dense = [
        (LineString([(0.0, 0.0), (10.0, 0.0)]), {"u": 0, "v": 1}),
        (LineString([(0.0, 0.0), (0.0, 10.0)]), {"u": 0, "v": 2}),
        (LineString([(0.0, 0.0), (-10.0, 0.0)]), {"u": 0, "v": 3}),
        (LineString([(0.0, 0.0), (0.0, -10.0)]), {"u": 0, "v": 4}),
    ]

    node_degree, node_adjacency, node_coords, node_branch_angles = _build_node_graph(merged_dense)
    node_types = _classify_intersection_nodes((node_adjacency, node_branch_angles))
    objects = _build_intersection_objects(
        node_types=node_types,
        adjacency=node_adjacency,
        node_coords=node_coords,
        node_branch_angles=node_branch_angles,
        node_branch_pitches={0: [0.0, 0.0, 0.0, 0.0]},
        node_branch_elevations={0: [0.0, 0.0, 0.0, 0.0]},
        to_local_fn=lambda x, y, z=None: (x, y),
        invert_y_axis=True,
        world_offset_x=0.0,
        world_offset_z=0.0,
    )

    assert len(objects) == 1
    assert objects[0].obj_type == "road-crossing"
    assert objects[0].x == 0.0
    assert objects[0].z == 0.0


def test_intersection_object_pitch_is_average_of_branch_slopes():
    merged_dense = [
        (LineString([(0.0, 0.0), (10.0, 0.1)]), {"u": 0, "v": 1}),
        (LineString([(0.0, 0.0), (-10.0, 0.1)]), {"u": 0, "v": 2}),
        (LineString([(0.0, 0.0), (0.0, 10.0)]), {"u": 0, "v": 3}),
    ]

    node_degree, node_adjacency, node_coords, node_branch_angles = _build_node_graph(merged_dense)
    node_types = _classify_intersection_nodes((node_adjacency, node_branch_angles))
    objects = _build_intersection_objects(
        node_types=node_types,
        adjacency=node_adjacency,
        node_coords=node_coords,
        node_branch_angles=node_branch_angles,
        node_branch_pitches={0: [0.5729, 0.5729, 0.0]},
        node_branch_elevations={0: [2.0, 3.0, 4.0]},
        to_local_fn=lambda x, y, z=None: (x, y),
        invert_y_axis=True,
        world_offset_x=0.0,
        world_offset_z=0.0,
    )

    assert len(objects) == 1
    assert abs(objects[0].pitch - (0.5729 + 0.5729 + 0.0) / 3) < 1e-4
    assert abs(objects[0].y - (2.0 + 3.0 + 4.0) / 3) < 1e-6


def test_best_cross_rotation_returns_branch_alignment():
    angles = [10.0, 100.0, 190.0, 280.0]
    rotation = _best_cross_rotation(angles)
    assert abs(rotation - 10.0) < 1e-6


def test_tee_orientation_angle_returns_perpendicular_branch():
    node = (0.0, 0.0)
    angles = [0.0, 180.0, 90.0]
    rotation = _tee_orientation_angle(angles, angle_tolerance=5.0)
    assert rotation == 90.0
