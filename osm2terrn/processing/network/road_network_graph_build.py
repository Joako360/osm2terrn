import math
from typing import Dict, List, Optional, Tuple

import geopandas as gpd


def _resolve_target_bounds_local(
    merged_dense: list,
    src_crs,
    local_crs,
    target_bounds: Optional[gpd.GeoDataFrame],
) -> tuple[float, float, float, float]:
    if target_bounds is not None:
        target_gdf = target_bounds
        if str(target_gdf.crs) != str(local_crs):
            target_gdf = target_gdf.to_crs(local_crs)
        minx, miny, maxx, maxy = target_gdf.total_bounds
        return float(minx), float(miny), float(maxx), float(maxy)

    geoms_gdf = gpd.GeoDataFrame(
        geometry=[geom for geom, _ in merged_dense],
        crs=src_crs,
    )
    geoms_local = geoms_gdf.to_crs(local_crs) if str(src_crs) != str(local_crs) else geoms_gdf
    minx, miny, maxx, maxy = geoms_local.total_bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def _build_node_degree(merged_dense: list) -> Dict[object, int]:
    node_degree: Dict[object, int] = {}
    for _line, attrs in merged_dense:
        u = attrs.get("u")
        v = attrs.get("v")
        if u is not None:
            node_degree[u] = node_degree.get(u, 0) + 1
        if v is not None:
            node_degree[v] = node_degree.get(v, 0) + 1
    return node_degree


def _vector_angle(vec: Tuple[float, float]) -> float:
    x, y = vec
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _build_node_graph(
    merged_dense: list,
) -> tuple[
    Dict[object, int],
    Dict[object, list],
    Dict[object, tuple[float, float]],
    Dict[object, list],
]:
    node_degree: Dict[object, int] = {}
    adjacency: Dict[object, list] = {}
    node_coords: Dict[object, tuple[float, float]] = {}
    node_branch_angles: Dict[object, list] = {}

    for line, attrs in merged_dense:
        u = attrs.get("u")
        v = attrs.get("v")
        if u is None or v is None:
            continue

        node_degree[u] = node_degree.get(u, 0) + 1
        node_degree[v] = node_degree.get(v, 0) + 1

        adjacency.setdefault(u, []).append(v)
        adjacency.setdefault(v, []).append(u)

        if line is not None and not line.is_empty:
            coords = list(line.coords)
            if coords:
                node_coords.setdefault(u, (coords[0][0], coords[0][1]))
                node_coords.setdefault(v, (coords[-1][0], coords[-1][1]))
            if len(coords) >= 2:
                start_vec = (coords[1][0] - coords[0][0], coords[1][1] - coords[0][1])
                end_vec = (coords[-2][0] - coords[-1][0], coords[-2][1] - coords[-1][1])
                node_branch_angles.setdefault(u, []).append(_vector_angle(start_vec))
                node_branch_angles.setdefault(v, []).append(_vector_angle(end_vec))

    return node_degree, adjacency, node_coords, node_branch_angles


def _classify_intersection_nodes(
    node_adjacency: Dict[object, list],
    node_branch_angles: Dict[object, list],
) -> Dict[object, str]:
    intersection_types: Dict[object, str] = {}
    for node_id, neighbors in node_adjacency.items():
        degree = len(neighbors)
        if degree == 3:
            intersection_types[node_id] = "tee"
        elif degree == 4:
            intersection_types[node_id] = "cross"
        elif degree >= 5:
            intersection_types[node_id] = "complex"
        else:
            intersection_types[node_id] = "other"
    return intersection_types
    

def _compute_branch_pitch(point_a: tuple[float, float, float], point_b: tuple[float, float, float]) -> float:
    dx = point_b[0] - point_a[0]
    dz = point_b[2] - point_a[2]
    dy = point_b[1] - point_a[1]
    horiz = math.hypot(dx, dz)
    return math.degrees(math.atan2(dy, horiz)) if horiz > 1e-6 else 0.0


def _compute_average_pitch(pitches: List[float]) -> float:
    return sum(pitches) / len(pitches) if pitches else 0.0


def _compute_average_elevation(elevations: List[float]) -> float:
    return sum(elevations) / len(elevations) if elevations else 0.0
