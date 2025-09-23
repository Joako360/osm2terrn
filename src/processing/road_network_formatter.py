from processing.road_model import Road
import osmnx as ox
from utils.geometry_utils import utm_crs_from_lonlat, densify_linestring
from data.osm_loader import load_graph, edges_to_lines
from processing.road_merger import merge_by_highway
from processing.road_exporters import (
    to_procedural_roads_block,
    to_intermediate_json,
    to_object_instance_lines,
    to_procedural_roads_blocks_per_segment,
)
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
            # LineString ya está en UTM, solo restar origen local
            X, Y = ls.xy
            raw_pts = [(float(x - x0), float(y - y0), 0.0) for x, y in zip(X, Y)]
        else:
            # LineString en WGS84, transformar a UTM y restar origen local
            ls_utm = shp_transform(to_utm_fn, ls)
            X, Y = ls_utm.xy
            raw_pts = [(float(x - x0), float(y - y0), 0.0) for x, y in zip(X, Y)]
        # Log primeros 3 puntos originales y transformados para diagnóstico
        if idx < 3:
            log_info(logger, f"Segment {idx} highway={attrs.get('highway')}, raw_pts={raw_pts[:3]}")
        # If elevation sampler is available, sample elevation in metric CRS before origin subtraction for Y
        if elev_sampler is not None:
            try:
                tree, elev_vals = elev_sampler
                # Recover metric XY (add origin back temporarily to query)
                metric_pts = [(px + x0, py + y0) for (px, py, _pz) in raw_pts]
                q = np.array(metric_pts, dtype=float)
                _dists, idxs = tree.query(q, k=1)
                elevs = elev_vals[idxs]
                raw_pts = [(px, py, float(ez)) for (px, py, _pz), ez in zip(raw_pts, elevs)]
            except Exception:
                pass
        pts = [pt for pt in raw_pts if all(map(math.isfinite, pt))]
        n_discarded = len(raw_pts) - len(pts)
        if n_discarded > 0:
            log_warning(logger, f"Discarded {n_discarded} non-finite points in road segment (highway={attrs.get('highway')})")
        if len(pts) < 2:
            log_warning(logger, f"Skipping road segment with <2 valid points (highway={attrs.get('highway')})")
            continue
        valid_segments += 1
        hw = attrs.get("highway")
        street_name = attrs.get("name")
        # Skip path-like types for road export (still available for terrain painting elsewhere)
        if str(hw) in {"cycleway", "footway", "path"}:
            continue
        try:
            roads.append(
                Road(
                    points_m=pts,
                    width=7.0,
                    border_width=0.0,
                    border_height=0.0,
                    kind=str(hw) if hw else "road",
                    name=str(street_name) if street_name else None,
                    is_bridge=bool(attrs.get("bridge", False)),
                )
            )
        except ValueError as e:
            log_warning(logger, f"Skipping road due to error: {e} (highway={hw})")
    log_info(logger, f"Total segments after filtering: {valid_segments}")
    # Export as instance lines with comments for street/bridge/tunnel
    output_dir = os.path.join(os.path.dirname(__file__), '../../output')
    os.makedirs(output_dir, exist_ok=True)
    tobj_path = os.path.join(output_dir, f'{tobj_prefix}_roads.tobj')
    from processing.road_exporters import to_object_instance_lines
    lines = []
    for r in roads:
        if r.name:
            lines.append(f"// OSM street: {r.name}")
        if getattr(r, "is_bridge", False):
            lines.append("// OSM: bridge=yes")
        lines.append("begin_procedural_roads")
        pts = r.points_m
        n = len(pts)
        from processing.road_exporters import map_osm_kind_to_ror
        obj_name = "roadbridge" if getattr(r, "is_bridge", False) else map_osm_kind_to_ror(r.kind, "road")
        for i, (x, z, y) in enumerate(pts):
            # Heading calculation
            if i < n - 1:
                nx, nz, _ = pts[i + 1]
                dx, dz = (nx - x), (nz - z)
            elif i > 0:
                px, pz, _ = pts[i - 1]
                dx, dz = (x - px), (z - pz)
            else:
                dx, dz = 1.0, 0.0
            from math import atan2, degrees
            heading_deg = degrees(atan2(dz, dx))
            rx = 0.0
            ry = heading_deg
            rz = 0.0
            y_val = float(y) if y is not None else 0.0
            line = (
                f"{x:.3f}, {y_val:.6f}, {z:.3f}, "
                f"{rx:.6f}, {ry:.6f}, {rz:.6f}, {obj_name}"
            )
            lines.append(line)
        lines.append("end_procedural_roads")
    with open(tobj_path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + "\n")
        if not lines:
            f.write("\n")
    return tobj_path