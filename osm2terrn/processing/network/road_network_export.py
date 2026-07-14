import os
from typing import Dict, List, Optional

import geopandas as gpd
from pyproj import Transformer

from osm2terrn.config.settings import get_program_config, get_project_config
from osm2terrn.data.osm_loader import edges_to_lines, load_graph
from osm2terrn.processing.roads.road_elevation import (
    build_dem_sampler,
    build_node_elevation_sampler,
    sample_segment_elevation,
)
from osm2terrn.processing.roads.road_exporters_utils import map_osm_type_to_ror
from osm2terrn.processing.roads.road_geometry import (
    build_oriented_points,
    to_local_xz,
    trim_linestring_between_intersections,
)
from osm2terrn.processing.roads.road_model import Road
from osm2terrn.processing.network.tobj_exporter import TobjExporter
from osm2terrn.processing.domain_bridge import road_to_domain_model
from osm2terrn.processing.network.road_network_graph_build import (
    _resolve_target_bounds_local,
    _build_node_graph,
    _compute_branch_pitch,
)
from osm2terrn.processing.network.road_network_graph_intersections import (
    _classify_intersection_nodes,
    _build_intersection_objects,
)
from osm2terrn.utils.geometry.crs import local_crs_from_lonlat
from osm2terrn.utils.logger import get_logger, log_info, log_warning

logger = get_logger("road_network_export")
_PROGRAM_CONFIG = get_program_config()
_PROJECT_CONFIG = get_project_config()


def build_roads_from_place(
    place: str,
    origin_lon: float,
    origin_lat: float,
    network_type: str = "drive",
    tobj_prefix: str = _PROGRAM_CONFIG.terrain_runtime.default_tobj_prefix,
    simplify: bool = True,
    min_elevation: float = 0.0,
    target_bounds: Optional[gpd.GeoDataFrame] = None,
) -> str:
    """
    Load OSM data for a place, build roads, and export them to a .tobj file.
    """
    graph = load_graph(place=place, network_type=network_type, simplify=simplify)
    geoms_attrs, src_crs = edges_to_lines(graph)
    merged_dense = geoms_attrs

    dem_sampler = build_dem_sampler(merged_dense, src_crs)
    node_elev_sampler = build_node_elevation_sampler(place, network_type, simplify)

    local_crs = local_crs_from_lonlat(origin_lon, origin_lat)
    to_local = Transformer.from_crs(src_crs or "EPSG:4326", local_crs, always_xy=True)
    to_local_fn = to_local.transform

    _resolve_target_bounds_local(
        merged_dense=merged_dense,
        src_crs=src_crs,
        local_crs=local_crs,
        target_bounds=target_bounds,
    )

    invert_y_axis = True
    world_offset_x = 0.0
    world_offset_z = 0.0

    log_info(logger, f"Local CRS used for export: {local_crs}")
    log_info(logger, "Origin local x0=0.0, z=0.0")

    node_degree, node_adjacency, node_coords, node_branch_angles = _build_node_graph(merged_dense)
    node_intersection_type = _classify_intersection_nodes((node_adjacency, node_branch_angles))
    node_branch_pitches: Dict[object, List[float]] = {}
    node_branch_elevations: Dict[object, List[float]] = {}
    t_count = sum(1 for node_type in node_intersection_type.values() if node_type == "tee")
    cross_count = sum(1 for node_type in node_intersection_type.values() if node_type == "cross")
    other_count = sum(1 for node_type in node_intersection_type.values() if node_type == "other")
    raw_t_count = sum(1 for deg in node_degree.values() if deg == 3)
    raw_cross_count = sum(1 for deg in node_degree.values() if deg == 4)
    complex_count = sum(1 for deg in node_degree.values() if deg >= 5)
    log_info(
        logger,
        f"Detected intersections: T={t_count} (raw deg3={raw_t_count}), X={cross_count} (raw deg4={raw_cross_count}), other={other_count}, complex(>=5)={complex_count}",
    )
    log_info(logger, f"Total segments before filtering: {len(merged_dense)}")

    valid_segments = 0
    roads = []
    domain_roads = []

    for idx, (line, attrs) in enumerate(merged_dense):
        u = attrs.get("u")
        v = attrs.get("v")
        du = node_degree.get(u, 0) if u is not None else 0
        dv = node_degree.get(v, 0) if v is not None else 0
        attrs["intersection_type_u"] = node_intersection_type.get(u)
        attrs["intersection_type_v"] = node_intersection_type.get(v)
        trimmed = trim_linestring_between_intersections(line, du, dv)
        if trimmed is None:
            continue

        local_xz = to_local_xz(
            line=trimmed,
            to_local_fn=to_local_fn,
            invert_y_axis=invert_y_axis,
            world_offset_x=world_offset_x,
            world_offset_z=world_offset_z,
        )
        if idx < 3:
            log_info(logger, f"Segment {idx} highway={attrs.get('highway')}, local_xz={local_xz[:3]}")

        sampled_z = sample_segment_elevation(
            local_xz=local_xz,
            invert_y_axis=invert_y_axis,
            min_elevation=min_elevation,
            local_crs=local_crs,
            dem_sampler=dem_sampler,
            elev_sampler=node_elev_sampler,
        )
        local_pts_m, yaw_list, pitch_list = build_oriented_points(local_xz, sampled_z)
        attrs["points_m"] = local_pts_m
        attrs["yaw_deg"] = yaw_list
        attrs["pitch_deg"] = pitch_list

        if len(local_pts_m) >= 2:
            if u is not None:
                node_branch_pitches.setdefault(u, []).append(_compute_branch_pitch(local_pts_m[0], local_pts_m[1]))
                node_branch_elevations.setdefault(u, []).append(local_pts_m[0][1])
            if v is not None:
                node_branch_pitches.setdefault(v, []).append(
                    _compute_branch_pitch(local_pts_m[-1], local_pts_m[-2])
                )
                node_branch_elevations.setdefault(v, []).append(local_pts_m[-1][1])

        valid_segments += 1
        highway = attrs.get("highway")
        if str(highway) in {"cycleway", "footway", "path"}:
            continue

        road_type = map_osm_type_to_ror(str(highway) if highway else "", "road")
        if attrs.get("bridge", False):
            road_type = "roadbridge"

        try:
            processing_road = Road(
                points_m=local_pts_m,
                width=_PROJECT_CONFIG.roads.default_width,
                border_width=_PROJECT_CONFIG.roads.default_border_width,
                border_height=_PROJECT_CONFIG.roads.default_border_height,
                type=road_type,
                name=str(attrs.get("name")) if attrs.get("name") else None,
                is_bridge=bool(attrs.get("bridge", False)),
                yaw_deg=yaw_list,
                pitch_deg=pitch_list,
                roll_deg=[0.0] * len(yaw_list),
            )
            roads.append(processing_road)
            domain_roads.append(road_to_domain_model(processing_road))
        except ValueError as exc:
            log_warning(logger, f"Skipping road due to error: {exc} (highway={highway})")

    log_info(logger, f"Total segments after filtering: {valid_segments}")
    intersection_objects = _build_intersection_objects(
        node_types=node_intersection_type,
        adjacency=node_adjacency,
        node_coords=node_coords,
        node_branch_angles=node_branch_angles,
        node_branch_pitches=node_branch_pitches,
        node_branch_elevations=node_branch_elevations,
        to_local_fn=to_local_fn,
        invert_y_axis=invert_y_axis,
        world_offset_x=world_offset_x,
        world_offset_z=world_offset_z,
    )
    if intersection_objects:
        log_info(logger, f"Will export {len(intersection_objects)} intersection objects")

    output_dir = os.path.join(os.path.dirname(__file__), "../../output")
    os.makedirs(output_dir, exist_ok=True)
    roads_filename = f"{tobj_prefix}_roads.tobj"
    exporter = TobjExporter(output_dir=output_dir)
    exporter.export_to_tobj(
        roads=roads,
        objects=intersection_objects if intersection_objects else None,
        collision_tris=None,
        filename=roads_filename,
        include_procedural_roads=True,
    )
    return os.path.join(output_dir, roads_filename)
