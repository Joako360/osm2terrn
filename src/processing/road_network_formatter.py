from processing.road_model import Road
import osmnx as ox
from typing import List, Optional, Tuple
from utils.geometry_utils import utm_crs_from_lonlat, densify_linestring
from data.osm_loader import load_graph, edges_to_lines
from processing.road_merger import merge_by_highway
from processing.road_exporters import map_osm_type_to_ror
from processing.tobj_exporter import TobjExporter

import os
import math

def build_roads_from_place(
    place: str,
    origin_lon: float,
    origin_lat: float,
    network_type: str = "drive",
    densify_step_m: float = 5.0,
    tobj_prefix: str = "terrain"
) -> str:
    """
    Loads OSM data for a given place, generates Road objects, and exports the procedural block to a .tobj file.

    Args:
        place (str): Name of the place to download OSM data for.
        origin_lon (float): Longitude of the local origin (center of terrain).
        origin_lat (float): Latitude of the local origin (center of terrain).
        network_type (str, optional): Type of road network to extract (default: "drive").
        densify_step_m (float, optional): Step size in meters for densifying road lines (default: 5.0).

    Returns:
        str: Path to the generated .tobj file containing procedural road definitions.
    """
    G = load_graph(place=place, network_type=network_type)
    geoms_attrs, src_crs = edges_to_lines(G)
    merged = merge_by_highway(geoms_attrs)
    merged_dense = [(densify_linestring(ls, densify_step_m), attrs) for ls, attrs in merged]
    # Build elevation sampler from original projected graph nodes if elevations are present
    import numpy as np
    elev_sampler = None
    try:
        # We need original metric graph nodes with possible 'elevation' attribute
        # Re-load with same inputs; project as in edges_to_lines
        G2 = load_graph(place=place, network_type=network_type)
        G2m = ox.project_graph(G2)
        node_coords = []
        node_elev = []
        for nid, nd in G2m.nodes(data=True):
            if 'x' in nd and 'y' in nd and ('elevation' in nd or 'elev' in nd):
                node_coords.append([float(nd['x']), float(nd['y'])])
                node_elev.append(float(nd.get('elevation', nd.get('elev', 0.0))))
        if node_coords:
            # Lazy import via importlib to avoid static symbol errors
            try:
                import importlib
                scipy_spatial = importlib.import_module('scipy.spatial')
                _CKD = getattr(scipy_spatial, 'cKDTree', None)
            except Exception:
                _CKD = None
            if _CKD is not None:
                tree = _CKD(np.array(node_coords, dtype=float))
                elev_vals = np.array(node_elev, dtype=float)
                elev_sampler = (tree, elev_vals)
    except Exception:
        elev_sampler = None
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    utm = utm_crs_from_lonlat(origin_lon, origin_lat)
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    to_utm_fn = lambda x, y, z=None: to_utm.transform(x, y)
    wgs84_to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    x0, y0 = wgs84_to_utm.transform(origin_lon, origin_lat)
    # Add local mapping options
    INVERT_Y_AXIS = True  # flip Y if your engine uses opposite northing
    WORLD_OFFSET_X = 0.0  # set to world_size_x / 2.0 if origin is top-left corner
    WORLD_OFFSET_Z = 0.0  # set to world_size_z / 2.0 if origin is top-left corner
    from utils.logger import get_logger, log_warning, log_info
    logger = get_logger("road_network_formatter")
    log_info(logger, f"CRS used for UTM: {utm}")
    log_info(logger, f"Origin local x0={x0}, y0={y0}")
    log_info(logger, f"Total segments before filtering: {len(merged_dense)}")
    valid_segments = 0
    roads = []
    # Detect if input CRS is already UTM (metric)
    is_utm = False
    if src_crs:
        try:
            crs_str = str(src_crs)
            is_utm = ("UTM" in crs_str or crs_str.startswith("EPSG:32"))
        except Exception:
            is_utm = False
    for idx, (ls, attrs) in enumerate(merged_dense):
        if is_utm:
            X, Y = ls.xy
        else:
            ls_utm = shp_transform(to_utm_fn, ls)
            X, Y = ls_utm.xy

        # Map to local XY (origin-centered), apply optional Y inversion and world offsets for corner-origin terrains
        local_xy = [(float(x - x0), float(y - y0)) for x, y in zip(X, Y)]
        if INVERT_Y_AXIS:
            local_xz = [(lx + WORLD_OFFSET_X, -ly + WORLD_OFFSET_Z) for lx, ly in local_xy]
        else:
            local_xz = [(lx + WORLD_OFFSET_X, ly + WORLD_OFFSET_Z) for lx, ly in local_xy]

        # Log primeros 3 puntos originales y transformados para diagnóstico
        if idx < 3:
            log_info(logger, f"Segment {idx} highway={attrs.get('highway')}, local_xz={local_xz[:3]}")

        # Sample elevation (Z vertical) if sampler is available
        local_pts_m: List[tuple] = []
        yaw_list: List[float] = []
        pitch_list: List[float] = []

        if elev_sampler is not None:
            try:
                tree, elev_vals = elev_sampler
                # Query in metric UTM space: add origin back temporarily
                metric_pts = [(px + x0, ( -pz if INVERT_Y_AXIS else pz ) + y0) for (px, pz) in local_xz]
                q = np.array(metric_pts, dtype=float)
                _dists, idxs = tree.query(q, k=1)
                sampled_z = elev_vals[idxs]  # elevation in meters
            except Exception:
                sampled_z = np.zeros(len(local_xz), dtype=float)
        else:
            sampled_z = np.zeros(len(local_xz), dtype=float)

        # Build points with Z as elevation, and compute yaw/pitch along the path
        import math
        for i, (px, pz) in enumerate(local_xz):
            # Vertical is Z per project conventions
            py = float(sampled_z[i])

            # Forward-difference tangent for yaw/pitch
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

            # Yaw around vertical axis (degrees)
            yaw_deg = math.degrees(math.atan2(dz, dx)) if (dx != 0.0 or dz != 0.0) else 0.0
            # Pitch from slope (degrees)
            horiz_len = math.hypot(dx, dz)
            pitch_deg = math.degrees(math.atan2(dy, horiz_len)) if horiz_len > 1e-6 else 0.0

            yaw_list.append(float(yaw_deg))
            pitch_list.append(float(pitch_deg))
            # Store point (X,Y,Z) with Z = elevation
            local_pts_m.append((float(px), float(py), float(pz)))

        # Attach computed points and orientations to attrs for downstream .tobj emission
        attrs["points_m"] = local_pts_m
        attrs["yaw_deg"] = yaw_list
        attrs["pitch_deg"] = pitch_list
        # Extract highway type and other attributes for road creation
        hw = attrs.get("highway")
        street_name = attrs.get("name")
        pts = local_pts_m
        valid_segments += 1
        # Skip path-like types for road export (still available for terrain painting elsewhere)
        if str(hw) in {"cycleway", "footway", "path"}:
            continue

        road_type = map_osm_type_to_ror(str(hw) if hw else "", "road")
        if attrs.get("bridge", False):
            road_type = "roadbridge"

        try:
            roads.append(
                Road(
                    points_m=pts,
                    width=7.0,
                    border_width=0.0,
                    border_height=0.0,
                    type=road_type,
                    name=str(street_name) if street_name else None,
                    is_bridge=bool(attrs.get("bridge", False)),
                )
            )
        except ValueError as e:
            log_warning(logger, f"Skipping road due to error: {e} (highway={hw})")
    log_info(logger, f"Total segments after filtering: {valid_segments}")
    # Export procedural roads using the centralized TobjExporter
    output_dir = os.path.join(os.path.dirname(__file__), '../../output')
    os.makedirs(output_dir, exist_ok=True)
    roads_filename = f"{tobj_prefix}_roads.tobj"
    exporter = TobjExporter(output_dir=output_dir)
    exporter.export_to_tobj(
        roads=roads,
        objects=None,
        collision_tris=None,
        filename=roads_filename,
        include_procedural_roads=True,
    )
    return os.path.join(output_dir, roads_filename)