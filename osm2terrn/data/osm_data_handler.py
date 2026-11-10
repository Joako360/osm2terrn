import re
from collections.abc import Callable
from dataclasses import replace
from typing import Any, Dict, Optional, Tuple

import geopandas as gpd
import fused
import networkx as nx
import osmnx as ox
from pyproj import CRS

from osm2terrn.cache.manager import CacheManager
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.adapters.bounds import require_domain_bounding_box
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.config.settings import get_program_config
from osm2terrn.adapters.coordinate_transform import transform_gdf_to_ror, transform_graph_to_ror
from osm2terrn.data.acquisition import (
    AcquisitionFailureCategory,
    AcquisitionFailureStage,
    LayerAcquisitionResult,
)
from osm2terrn.data.overpass import call_with_retries
from osm2terrn.data.street_network import StreetNetworkResult
from osm2terrn.utils.logger import get_logger, log_error, log_info, log_warning

logger = get_logger("osm_data_handler")
_OSM_BBOX_CACHE_NAMESPACE = "providers/osm/bbox-bundle"
_OSM_BBOX_ALGORITHM_VERSION = "5"
_OSM_LAYER_CACHE_NAMESPACE = "providers/osm/bbox-layers"
_OSM_LAYER_CACHE_ALGORITHM_VERSION = "1"
_OVERTURE_BUILDINGS_CACHE_NAMESPACE = "providers/overture/buildings"
_OVERTURE_BUILDINGS_ALGORITHM_VERSION = "1"
_ACQUISITION_RESULTS_KEY = "acquisition_results"

_PROGRAM_CONFIG = get_program_config()
_DEFAULT_GEOMETRY_LAYERS = frozenset(_PROGRAM_CONFIG.osm.map_geometries)
custom_tags = list(_PROGRAM_CONFIG.osm.custom_tags)
map_geometries = dict(_PROGRAM_CONFIG.osm.map_geometries)
networks = dict(_PROGRAM_CONFIG.osm.networks)

ox.settings.elevation_url_template = _PROGRAM_CONFIG.providers.elevation_url_template # type: ignore
ox.settings.log_console = _PROGRAM_CONFIG.osm.osmnx_log_console # type: ignore
ox.settings.log_file = _PROGRAM_CONFIG.osm.osmnx_log_file # type: ignore
ox.settings.log_level = _PROGRAM_CONFIG.osm.osmnx_log_level # type: ignore
ox.settings.overpass_url = _PROGRAM_CONFIG.osm.overpass_endpoints[0]
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


def _bbox_to_osmnx_tuple(bounds: BoundingBox) -> tuple[float, float, float, float]:
    """Return (west, south, east, north) in EPSG:4326 for OSMnx requests."""
    bbox = bounds.reproject("EPSG:4326") if bounds.crs and bounds.crs != "EPSG:4326" else bounds
    return (bbox.west, bbox.south, bbox.east, bbox.north)


def _http_status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is None:
        status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    match = re.search(
        r"(?:responded:\s*|HTTP(?:\s+status\s+code)?|status(?:\s+code)?)\s*[:=]?\s*(\d{3})",
        str(exc),
        flags=re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def _layer_failure(
    exc: Exception,
    *,
    stage: AcquisitionFailureStage,
) -> LayerAcquisitionResult:
    status_code = _http_status_code(exc)
    if status_code is not None and (
        status_code in {408, 425, 429} or 500 <= status_code <= 599
    ):
        category: AcquisitionFailureCategory = "temporary"
    elif status_code is not None and 400 <= status_code <= 499:
        category = "permanent"
    elif any(
        cls.__name__
        in {"Timeout", "ConnectionError", "ConnectTimeoutError", "ReadTimeoutError"}
        for cls in type(exc).__mro__
    ):
        category = "temporary"
    else:
        category = "unknown"

    diagnostic = type(exc).__name__
    if status_code is not None:
        diagnostic = f"{diagnostic} (HTTP {status_code})"
    return LayerAcquisitionResult(
        status="failed",
        failure_category=category,
        failure_stage=stage,
        diagnostic=diagnostic,
    )


def _is_no_matching_features(exc: Exception) -> bool:
    return (
        type(exc).__name__ == "InsufficientResponseError"
        and "no matching features" in str(exc).casefold()
    )


def _layer_cache_key(
    cache_manager: CacheManager,
    bbox: BoundingBox,
    *,
    layer: str,
    layer_type: str,
    query: object,
) -> str:
    return cache_manager.build_key(
        {
            "bbox": list(bbox.to_tuple()),
            "bbox_crs": str(bbox.crs or ""),
            "bbox_is_projected": bool(getattr(bbox, "is_projected", False)),
            "layer": layer,
            "layer_type": layer_type,
            "query": query,
            "custom_tags": custom_tags,
            "bbox_algorithm_version": _OSM_BBOX_ALGORITHM_VERSION,
        },
        provider="osm",
        algorithm_version=_OSM_LAYER_CACHE_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="osm_bbox_layer",
    )


def _get_cached_layer(
    cache_manager: CacheManager,
    *,
    key: str,
    layer: str,
    layer_type: str,
) -> tuple[Any, LayerAcquisitionResult | StreetNetworkResult] | None:
    try:
        cached = cache_manager.get(
            namespace=_OSM_LAYER_CACHE_NAMESPACE,
            key=key,
            serializer=PickleSerializer[Dict](),
        )
    except Exception as exc:
        log_warning(
            logger,
            f"Ignoring invalid OSM layer cache for {layer} "
            f"({type(exc).__name__}); querying provider.",
        )
        return None
    if cached is None:
        return None

    payload = cached[0]
    try:
        if not isinstance(payload, dict) or payload.get("status") not in {"available", "empty"}:
            raise ValueError("Invalid cached layer status")
        data = payload.get("data")
        result = payload.get("result")
        if layer_type == "roads":
            if not isinstance(result, StreetNetworkResult):
                raise ValueError("Cached road layer has an invalid result")
            result.validate()
            if result.status not in {"available", "empty"}:
                raise ValueError("Cached road layer is not successful")
            return data, replace(result, source="cache")

        if not isinstance(result, LayerAcquisitionResult):
            raise ValueError("Cached layer has an invalid acquisition result")
        if result.status not in {"available", "empty"}:
            raise ValueError("Cached layer is not successful")
        if layer_type == "geometry":
            if result.status == "available" and not isinstance(data, gpd.GeoDataFrame):
                raise ValueError("Cached geometry layer has no GeoDataFrame")
            if result.status == "empty" and data is not None:
                raise ValueError("Cached empty geometry layer contains data")
        elif result.status == "available" and not isinstance(data, nx.MultiDiGraph):
            raise ValueError("Cached network layer has no graph")
        elif result.status == "empty" and data is not None:
            raise ValueError("Cached empty network layer contains data")
        return data, replace(result, source="cache")
    except Exception as exc:
        log_warning(
            logger,
            f"Ignoring invalid OSM layer cache for {layer} "
            f"({type(exc).__name__}); querying provider.",
        )
        return None


def _cache_layer(
    cache_manager: CacheManager,
    *,
    key: str,
    layer: str,
    layer_type: str,
    data: object,
    result: LayerAcquisitionResult | StreetNetworkResult,
) -> None:
    if result.status not in {"available", "empty"}:
        return
    try:
        cache_manager.put(
            namespace=_OSM_LAYER_CACHE_NAMESPACE,
            key=key,
            value={"status": result.status, "data": data, "result": result},
            serializer=PickleSerializer[Dict](),
            metadata=CacheMetadata(
                artifact_type="osm_bbox_layer",
                provider="osm",
                algorithm_version=_OSM_LAYER_CACHE_ALGORITHM_VERSION,
                format_version="1",
                extra={"layer": layer, "layer_type": layer_type, "status": result.status},
            ),
        )
    except Exception as exc:
        log_warning(
            logger,
            f"Could not cache successful OSM layer {layer} ({type(exc).__name__}).",
        )


def _query_osm_layer(request: Callable[[], Any]) -> Any:
    """Run one layer request with the configured bounded Overpass policy."""
    config = _PROGRAM_CONFIG.osm
    return call_with_retries(
        request,
        endpoints=config.overpass_endpoints,
        max_attempts=config.overpass_max_attempts,
        max_elapsed_seconds=config.overpass_max_elapsed_seconds,
    )


def download_data_from_bbox(bbox) -> Dict:
    """
    Downloads and processes OSM data using a bounding box only.
    Args:
        bbox (Tuple): (west, south, east, north)
    Returns a dict with keys:
      - bounds (domain BoundingBox in EPSG:4326)
      - x_0, y_0 (centroid of projected bounds)
      - one entry per geometry type in map_geometries (or None)
      - one entry per network in networks
      - acquisition_results, with a status for each configured geometry and non-road network
    """
    d: Dict = {}
    bbox_obj = require_domain_bounding_box(bbox)
    use_bbox = bbox_obj
    if bbox_obj.crs and bbox_obj.crs != "EPSG:4326":
        try:
            use_bbox = bbox_obj.reproject("EPSG:4326")
            log_info(logger, "Reprojected bbox to EPSG:4326 for OSM queries.")
        except Exception as e:
            log_warning(logger, f"Could not reproject bbox to EPSG:4326: {e} — attempting to use original bbox (may be incorrect).")

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
        format_version="3",
        artifact_type="osm_bbox_bundle",
    )
    acquisition_results: dict[str, LayerAcquisitionResult] = {
        layer: LayerAcquisitionResult(status="not_requested", source="none")
        for layer in _DEFAULT_GEOMETRY_LAYERS - set(map_geometries)
    }
    cache_recovered = False
    try:
        cached_bundle = cache_manager.get(
            namespace=_OSM_BBOX_CACHE_NAMESPACE,
            key=cache_key,
            serializer=serializer,
        )
    except Exception as exc:
        log_warning(logger, f"Ignoring invalid OSM bbox cache entry ({type(exc).__name__}); querying provider.")
        cached_bundle = None
        cache_recovered = True
    if cached_bundle is not None:
        cached_data = cached_bundle[0]
        try:
            if not isinstance(cached_data, dict):
                raise ValueError("Cached OSM bundle is not a dictionary")
            street_result = cached_data.get("roads")
            if not isinstance(street_result, StreetNetworkResult):
                raise ValueError("Cached roads entry does not use the current street contract")
            street_result.validate()
            cached_results = cached_data.get(_ACQUISITION_RESULTS_KEY)
            if not isinstance(cached_results, dict) or any(
                not isinstance(result, LayerAcquisitionResult)
                for result in cached_results.values()
            ):
                raise ValueError("Cached OSM bundle has no valid layer acquisition results")
        except Exception as exc:
            log_warning(logger, f"Ignoring invalid OSM bbox bundle ({type(exc).__name__}); querying provider.")
            cached_bundle = None
            cache_recovered = True
        else:
            cached_data["roads"] = replace(street_result, source="cache")
            cached_data[_ACQUISITION_RESULTS_KEY] = {
                name: (
                    result
                    if result.status == "not_requested"
                    else replace(result, source="cache")
                )
                for name, result in cached_results.items()
            }
            log_info(logger, "Loaded OSM bbox bundle from cache.")
            return cached_data

    west, south, east, north = _bbox_to_osmnx_tuple(use_bbox)
    # Find origin point in centroid
    # If bbox had an explicit CRS, use it; otherwise default to EPSG:4326
    try:
        # For axis-aligned bbox in EPSG:4326 the center is the midpoint of bounds.
        origin_lon = float((west + east) / 2.0)
        origin_lat = float((south + north) / 2.0)
    except Exception:
        log_error(logger, "Could not compute geographic centroid; defaulting origin to (0,0).")
        origin_lon, origin_lat = 0.0, 0.0
    d['bounds'] = BoundingBox(west, south, east, north, crs="EPSG:4326", is_projected=False)
    d['x_0'] = 0.0
    d['y_0'] = 0.0
    d['origin_lon'] = origin_lon
    d['origin_lat'] = origin_lat

    # Download simple geometries (use bbox-based query in lat/lon)
    # Note: osmnx expects (west, south, east, north)
    for typ, tag in map_geometries.items():
        layer_key = _layer_cache_key(
            cache_manager,
            use_bbox,
            layer=typ,
            layer_type="geometry",
            query=tag,
        )
        cached_layer = _get_cached_layer(
            cache_manager,
            key=layer_key,
            layer=typ,
            layer_type="geometry",
        )
        if cached_layer is not None:
            d[typ], cached_result = cached_layer
            if isinstance(cached_result, LayerAcquisitionResult):
                acquisition_results[typ] = cached_result
            continue
        try:
            # use bbox query in lat/lon (west, south, east, north)
            gdf = _query_osm_layer(
                lambda: ox.features_from_bbox((west, south, east, north), tags=tag)  # type: ignore
            )
        except Exception as exc:
            if _is_no_matching_features(exc):
                d[typ] = None
                acquisition_results[typ] = LayerAcquisitionResult(
                    status="empty",
                    diagnostic=None,
                )
                _cache_layer(
                    cache_manager,
                    key=layer_key,
                    layer=typ,
                    layer_type="geometry",
                    data=None,
                    result=acquisition_results[typ],
                )
                continue
            result = _layer_failure(exc, stage="acquisition")
            acquisition_results[typ] = result
            d[typ] = None
            log_warning(
                logger,
                f"Could not acquire geometry layer {typ}: {result.diagnostic} "
                f"(category={result.failure_category}).",
            )
            continue

        if gdf is None or gdf.empty:
            d[typ] = None
            acquisition_results[typ] = LayerAcquisitionResult(status="empty")
            _cache_layer(
                cache_manager,
                key=layer_key,
                layer=typ,
                layer_type="geometry",
                data=None,
                result=acquisition_results[typ],
            )
        else:
            try:
                d[typ] = transform_gdf_to_ror(gdf, origin_lon, origin_lat)
                acquisition_results[typ] = LayerAcquisitionResult(status="available")
                _cache_layer(
                    cache_manager,
                    key=layer_key,
                    layer=typ,
                    layer_type="geometry",
                    data=d[typ],
                    result=acquisition_results[typ],
                )
            except Exception as exc:
                result = _layer_failure(exc, stage="transformation")
                acquisition_results[typ] = result
                d[typ] = None
                log_warning(
                    logger,
                    f"Could not transform geometry layer {typ}: {result.diagnostic}.",
                )

    # Download simple networks (graph_from_bbox expects west, south, east, north)
    for typ, cf in networks.items():
        layer_type = "roads" if typ == "roads" else "network"
        layer_key = _layer_cache_key(
            cache_manager,
            use_bbox,
            layer=typ,
            layer_type=layer_type,
            query={
                "custom_filter": cf,
                "network_type": "drive",
                "simplify": False,
                "retain_all": True,
            },
        )
        cached_layer = _get_cached_layer(
            cache_manager,
            key=layer_key,
            layer=typ,
            layer_type=layer_type,
        )
        if cached_layer is not None:
            data, cached_result = cached_layer
            d[typ] = cached_result if typ == "roads" else data
            if typ != "roads" and isinstance(cached_result, LayerAcquisitionResult):
                acquisition_results[typ] = cached_result
            continue
        try:
            G = _query_osm_layer(
                lambda: ox.graph_from_bbox(
                    (west, south, east, north),
                    network_type="drive",
                    simplify=False,
                    retain_all=True,
                    custom_filter=cf,
                )
            )
            if typ == "roads":
                source = "cache_recovered" if cache_recovered else "query"
                if G is None or len(G.nodes) == 0:
                    d[typ] = StreetNetworkResult(status="empty", source=source)
                else:
                    # Nodes without edges stay as "empty" but keep the transformed graph.
                    transformed_graph = transform_graph_to_ror(G, origin_lon, origin_lat)
                    graph_crs = transformed_graph.graph.get("crs")
                    if graph_crs is None:
                        raise ValueError("Transformed street graph has no CRS")
                    d[typ] = StreetNetworkResult(
                        status="available" if transformed_graph.number_of_edges() > 0 else "empty",
                        graph=transformed_graph,
                        graph_crs=CRS.from_user_input(graph_crs).to_string(),
                        source=source,
                    )
                _cache_layer(
                    cache_manager,
                    key=layer_key,
                    layer=typ,
                    layer_type=layer_type,
                    data=d[typ],
                    result=d[typ],
                )
            elif G is None or len(G.nodes) == 0:
                d[typ] = None
                acquisition_results[typ] = LayerAcquisitionResult(status="empty")
                _cache_layer(
                    cache_manager,
                    key=layer_key,
                    layer=typ,
                    layer_type=layer_type,
                    data=None,
                    result=acquisition_results[typ],
                )
            else:
                try:
                    d[typ] = transform_graph_to_ror(G, origin_lon, origin_lat)
                    acquisition_results[typ] = LayerAcquisitionResult(status="available")
                    _cache_layer(
                        cache_manager,
                        key=layer_key,
                        layer=typ,
                        layer_type=layer_type,
                        data=d[typ],
                        result=acquisition_results[typ],
                    )
                except Exception as exc:
                    result = _layer_failure(exc, stage="transformation")
                    acquisition_results[typ] = result
                    d[typ] = None
                    log_warning(
                        logger,
                        f"Could not transform network layer {typ}: {result.diagnostic}.",
                    )
        except Exception as exc:
            if typ == "roads":
                failure = _layer_failure(exc, stage="acquisition")
                diagnostic = (
                    f"{failure.diagnostic}: street acquisition or CRS transformation failed "
                    f"(category={failure.failure_category})"
                )
                log_warning(logger, diagnostic)
                d[typ] = StreetNetworkResult(
                    status="failed",
                    diagnostic=diagnostic,
                    source="cache_recovered" if cache_recovered else "query",
                )
            else:
                result = _layer_failure(exc, stage="acquisition")
                acquisition_results[typ] = result
                log_warning(
                    logger,
                    f"Could not acquire network layer {typ}: {result.diagnostic} "
                    f"(category={result.failure_category}).",
                )
                d[typ] = None

    if "roads" not in networks:
        d["roads"] = StreetNetworkResult(status="not_requested", source="none")

    d[_ACQUISITION_RESULTS_KEY] = acquisition_results
    has_failed_layer = any(
        result.status == "failed" for result in acquisition_results.values()
    ) or d["roads"].status == "failed"
    if has_failed_layer:
        log_info(logger, "Skipping OSM bbox cache write because at least one requested layer failed.")
    else:
        cache_manager.put(
            namespace=_OSM_BBOX_CACHE_NAMESPACE,
            key=cache_key,
            value=d,
            serializer=serializer,
            metadata=CacheMetadata(
                artifact_type="osm_bbox_bundle",
                provider="osm",
                algorithm_version=_OSM_BBOX_ALGORITHM_VERSION,
                format_version="3",
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
    bbox_obj = require_domain_bounding_box(bbox)
    west, south, east, north = _bbox_to_osmnx_tuple(bbox_obj)
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
        'bbox': (west, south, east, north),
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
