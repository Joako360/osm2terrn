import logging
import geopandas as gpd
import fused
import osmnx as ox
from typing import Dict, Tuple, Optional
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.entities.bbox import BBox
from osm2terrn.config.settings import get_program_config
from osm2terrn.adapters.coordinate_transform import transform_gdf_to_ror, transform_graph_to_ror
from osm2terrn.utils.logger import get_logger, log_error, log_info, log_warning

logger = get_logger("osm_data_handler")
_OSM_BBOX_CACHE_NAMESPACE = "providers/osm/bbox-bundle"
_OSM_BBOX_ALGORITHM_VERSION = "1"
_OVERTURE_BUILDINGS_CACHE_NAMESPACE = "providers/overture/buildings"
_OVERTURE_BUILDINGS_ALGORITHM_VERSION = "1"

_PROGRAM_CONFIG = get_program_config()
custom_tags = list(_PROGRAM_CONFIG.osm.custom_tags)
map_geometries = dict(_PROGRAM_CONFIG.osm.map_geometries)
networks = dict(_PROGRAM_CONFIG.osm.networks)

ox.settings.elevation_url_template = _PROGRAM_CONFIG.providers.elevation_url_template # type: ignore
ox.settings.log_console = _PROGRAM_CONFIG.osm.osmnx_log_console # type: ignore
ox.settings.log_file = _PROGRAM_CONFIG.osm.osmnx_log_file # type: ignore
ox.settings.log_level = _PROGRAM_CONFIG.osm.osmnx_log_level # type: ignore
ox.settings.useful_tags_way = ox.settings.useful_tags_way + custom_tags # type: ignore
# Reduce query size to encourage osmnx to split large areas into smaller Overpass queries
try:
    ox.settings.max_query_area_size = _PROGRAM_CONFIG.osm.max_query_area_size  # type: ignore
except Exception:
    pass
# Tweak request timeout to fail faster on unresponsive endpoints
try:
    ox.settings.requests_timeout = _PROGRAM_CONFIG.osm.requests_timeout  # type: ignore
except Exception:
    pass
# Allow users to override overpass rate limiting (default True = be nice)
try:
    ox.settings.overpass_rate_limit = _PROGRAM_CONFIG.osm.overpass_rate_limit  # type: ignore
except Exception:
    pass
ox.__version__
# Example: custom_filter='["railway"~"tram|rail"]'


def download_data_from_bbox(bbox) -> Dict:
    """
    Downloads and processes OSM data using a bounding box only.
    Args:
        bbox (Tuple): (west, south, east, north)
    Returns a dict with keys:
      - bounds (GeoDataFrame EPSG:4326)
      - bounds_proj (GeoDataFrame in EPSG:3857)
      - x_0, y_0 (centroid of projected bounds)
      - one entry per geometry type in map_geometries (or None)
      - one entry per network in networks (or None)
    """
    d: Dict = {}
    # Accept tuple/list or any bbox-like; use BBox helper for parsing/validation
    bbox_obj = BBox(bbox)
    # If bbox is projected, osmnx expects geographic coords — try to reproject
    if getattr(bbox_obj, "is_projected", False):
        try:
            bbox_geo = bbox_obj.reproject("EPSG:4326")
            use_bbox = bbox_geo
            log_info(logger, "Reprojected bbox to EPSG:4326 for OSM queries.")
        except Exception as e:
            log_warning(logger, f"Could not reproject bbox to EPSG:4326: {e} — attempting to use original bbox (may be incorrect).")
            use_bbox = bbox_obj
    else:
        use_bbox = bbox_obj

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[Dict]()
    cache_key = cache_manager.build_key(
        {
            "bbox": list(use_bbox.to_tuple()),
            "bbox_is_projected": bool(getattr(bbox_obj, "is_projected", False)),
            "bbox_crs": str(getattr(bbox_obj, "crs", "") or ""),
            "map_geometries": map_geometries,
            "networks": networks,
            "custom_tags": custom_tags,
        },
        provider="osm",
        algorithm_version=_OSM_BBOX_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="osm_bbox_bundle",
    )
    cached_bundle = cache_manager.get(
        namespace=_OSM_BBOX_CACHE_NAMESPACE,
        key=cache_key,
        serializer=serializer,
    )
    if cached_bundle is not None:
        log_info(logger, "Loaded OSM bbox bundle from cache.")
        return cached_bundle[0]

    # prefer BBox.to_shapely() to keep single parsing point
    polygon = use_bbox.to_shapely()
    west, south, east, north = use_bbox.to_tuple()
    # Find origin point in centroid
    # If bbox had an explicit CRS, use it; otherwise default to EPSG:4326
    gdf_crs = bbox_obj.crs if bbox_obj.crs is not None else "EPSG:4326"
    bounds_gdf = gpd.GeoDataFrame(geometry=[polygon], crs=gdf_crs)
    bounds_proj = bounds_gdf.to_crs(3857)
    try:
        # For axis-aligned bbox in EPSG:4326 the center is the midpoint of bounds.
        origin_lon = float((west + east) / 2.0)
        origin_lat = float((south + north) / 2.0)
    except Exception:
        log_error(logger, "Could not compute geographic centroid; defaulting origin to (0,0).")
        origin_lon, origin_lat = 0.0, 0.0
    d['bounds'] = bounds_gdf.to_crs(4326)
    d['bounds_proj'] = bounds_proj
    d['x_0'] = 0.0
    d['y_0'] = 0.0
    d['origin_lon'] = origin_lon
    d['origin_lat'] = origin_lat

    # Download simple geometries (use bbox-based query in lat/lon)
    # Note: osmnx expects (west, south, east, north)
    for typ, tag in map_geometries.items():
        try:
            # use bbox query in lat/lon (west, south, east, north)
            gdf = ox.features_from_bbox(west, south, east, north, tags=tag)  # type: ignore
            if gdf is None or gdf.empty:
                d[typ] = None
            else:
                d[typ] = transform_gdf_to_ror(gdf, origin_lon, origin_lat)
        except Exception as exc:
            log_info(logger, f"Skipped geometry {typ} due to error: {exc}")
            d[typ] = None

    # Download simple networks (graph_from_bbox expects west, south, east, north)
    for typ, cf in networks.items():
        try:
            G = ox.graph_from_bbox(
                (west, south, east, north),
                network_type="drive",
                simplify=False,
                retain_all=True,
                custom_filter=cf
            )
            if G is None or len(G.nodes) == 0:
                d[typ] = None
            else:
                d[typ] = transform_graph_to_ror(G, origin_lon, origin_lat)
        except Exception as exc:
            log_info(logger, f"Skipped network {typ} due to error: {exc}")
            d[typ] = None

    cache_manager.put(
        namespace=_OSM_BBOX_CACHE_NAMESPACE,
        key=cache_key,
        value=d,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="osm_bbox_bundle",
            provider="osm",
            algorithm_version=_OSM_BBOX_ALGORITHM_VERSION,
            format_version="1",
            extra={
                "geometry_types": sorted(map_geometries.keys()),
                "network_types": sorted(networks.keys()),
            },
        ),
    )

    return d


# Download graph from OSM with osmnx parameters: place query, which option and optional custom filters

def download_menu() -> Tuple[Optional[str], Optional[Tuple[float, float, float, float]]]:
    """
    Shows a menu to choose between searching by city name or entering bounding box manually.
    Returns:
     - A tuple of (place_name, bbox) when a selection is made.
     - If the user cancels, returns ("", None).
    """
    from osm2terrn.data.download_menu import DownloadMenu

    menu = DownloadMenu()
    return menu.show_main_menu()


def download_builings_from_overture(bbox) -> gpd.GeoDataFrame:
    """
    Downloads building geometries from the Overture Maps dataset within a specified bounding box.

    Args:
        bbox (list or tuple): Bounding box coordinates in the format [min_lon, min_lat, max_lon, max_lat].

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing building geometries and associated attributes, 
        with the coordinate reference system set to EPSG:4326.

    Raises:
        Exception: If the data download or processing fails.
    """
    bbox_obj = BBox(bbox)
    cache_manager = get_cache_manager()
    serializer = PickleSerializer[gpd.GeoDataFrame]()
    cache_key = cache_manager.build_key(
        {
            "bbox": list(bbox_obj.to_tuple()),
            "bbox_is_projected": bool(getattr(bbox_obj, "is_projected", False)),
            "bbox_crs": str(getattr(bbox_obj, "crs", "") or ""),
            "overture_type": "building",
        },
        provider="overture",
        algorithm_version=_OVERTURE_BUILDINGS_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="buildings_geodataframe",
    )
    cached = cache_manager.get(
        namespace=_OVERTURE_BUILDINGS_CACHE_NAMESPACE,
        key=cache_key,
        serializer=serializer,
    )
    if cached is not None:
        log_info(logger, "Loaded Overture buildings from cache.")
        return cached[0]

    udf = fused.load("https://github.com/fusedio/udfs/tree/main/public/Overture_Maps_Example")
    param = {
        'bbox': bbox,
        'overture_type': 'building',
    }
    gdf_output = fused.run(udf, parameters=param) # type: ignore
    gdf = gpd.GeoDataFrame(gdf_output, geometry='geometry', crs='epsg:4326')
    cache_manager.put(
        namespace=_OVERTURE_BUILDINGS_CACHE_NAMESPACE,
        key=cache_key,
        value=gdf,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="buildings_geodataframe",
            provider="overture",
            algorithm_version=_OVERTURE_BUILDINGS_ALGORITHM_VERSION,
            format_version="1",
            extra={"feature_count": int(len(gdf))},
        ),
    )
    return gdf