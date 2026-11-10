from typing import List, Optional, Tuple

import geopandas as gpd
import numpy as np

from osm2terrn.processing.terrain.elevation_service import load_elevation_raster, sample_elevation_at_coords
from osm2terrn.utils.logger import get_logger, log_info, log_warning

logger = get_logger("road_elevation")


def build_dem_sampler(merged_dense: list, src_crs) -> Optional[tuple]:
    """Build DEM sampler tuple `(elevation, transform)` for the road network extent."""
    try:
        geoms_gdf = gpd.GeoDataFrame(
            geometry=[geom for geom, _ in merged_dense],
            crs=src_crs,
        )
        if geoms_gdf.crs is None:
            raise ValueError("Cannot determine CRS for road geometries")
        geoms_geo = geoms_gdf.to_crs("EPSG:4326") if str(src_crs) != "EPSG:4326" else geoms_gdf
        west, south, east, north = map(float, geoms_geo.total_bounds)
        dem_elevation, dem_transform, dem_max, dem_min = load_elevation_raster(
            {
                "west": west,
                "south": south,
                "east": east,
                "north": north,
            }
        )
        log_info(logger, f"Loaded DEM for road heights: min={dem_min:.2f}m, max={dem_max:.2f}m")
        return dem_elevation, dem_transform
    except Exception as exc:
        log_warning(logger, f"DEM height sampling unavailable: {exc}")
        return None


def build_node_elevation_sampler(
    place: str,
    network_type: str,
    simplify: bool,
) -> Optional[tuple]:
    """Build fallback nearest-node elevation sampler tuple `(tree, elev_vals)`."""
    try:
        from data.osm_loader import load_graph

        graph = load_graph(place=place, network_type=network_type, simplify=simplify)
        node_coords = []
        node_elev = []
        for _, node_data in graph.nodes(data=True):
            if "x" in node_data and "y" in node_data and ("elevation" in node_data or "elev" in node_data):
                node_coords.append([float(node_data["x"]), float(node_data["y"])])
                node_elev.append(float(node_data.get("elevation", node_data.get("elev", 0.0))))
        if not node_coords:
            return None

        try:
            import importlib

            scipy_spatial = importlib.import_module("scipy.spatial")
            ckd_tree = getattr(scipy_spatial, "cKDTree", None)
        except Exception:
            ckd_tree = None

        if ckd_tree is None:
            return None
        tree = ckd_tree(np.array(node_coords, dtype=float))
        elev_vals = np.array(node_elev, dtype=float)
        return tree, elev_vals
    except Exception:
        return None


def sample_segment_elevation(
    local_xz: List[Tuple[float, float]],
    invert_y_axis: bool,
    min_elevation: float,
    local_crs,
    dem_sampler,
    elev_sampler,
) -> np.ndarray:
    """Sample elevation for local segment points using DEM or graph node fallback."""
    from pyproj import Transformer

    metric_pts = [(px, (-pz if invert_y_axis else pz)) for (px, pz) in local_xz]
    xs = np.array([pt[0] for pt in metric_pts], dtype=float)
    ys = np.array([pt[1] for pt in metric_pts], dtype=float)
    wgs84_from_local = Transformer.from_crs(local_crs, "EPSG:4326", always_xy=True)
    lons, lats = wgs84_from_local.transform(xs, ys)

    if dem_sampler is not None:
        try:
            sampled = sample_elevation_at_coords(np.asarray(lons), np.asarray(lats), *dem_sampler)
            return sampled - min_elevation
        except Exception:
            return np.zeros(len(local_xz), dtype=float)

    if elev_sampler is not None:
        try:
            tree, elev_vals = elev_sampler
            query = np.column_stack((lons, lats))
            _dists, idxs = tree.query(query, k=1)
            return elev_vals[idxs] - min_elevation
        except Exception:
            return np.zeros(len(local_xz), dtype=float)

    return np.zeros(len(local_xz), dtype=float)
