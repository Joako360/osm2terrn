from io import BytesIO
import os
from typing import Any, Dict

import numpy as np
import rasterio
import requests
from rasterio.transform import rowcol

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_error, log_info, log_warning

logger = get_logger("elevation_service")
_PROGRAM_CONFIG = get_program_config()
_ELEVATION_CACHE_NAMESPACE = "providers/elevation/raster"
_ELEVATION_CACHE_ALGORITHM_VERSION = "1"


def _mask_api_key(api_key: str) -> str:
    """Return a safe representation of the API key for logs."""
    if api_key and len(api_key) > 6:
        return api_key[:3] + "..." + api_key[-3:]
    return "(OpenTopography API key invalid or missing)"


def _normalize_bbox_for_api(bounds: Any) -> BoundingBox:
    """Normalize an input bounds object to EPSG:4326 bbox for OpenTopography."""
    try:
        bbox_obj = bounds if isinstance(bounds, BoundingBox) else BoundingBox(bounds)
    except Exception as exc:
        log_error(logger, f"Invalid bbox for elevation API: {exc}")
        raise

    if getattr(bbox_obj, "is_projected", False):
        try:
            bbox_obj = bbox_obj.reproject("EPSG:4326")
            log_info(logger, "Reprojected bbox to EPSG:4326 for elevation API.")
        except Exception as exc:
            log_warning(
                logger,
                "Could not reproject bbox to EPSG:4326: "
                f"{exc}. Proceeding with original bbox (may be incorrect for the API).",
            )
    return bbox_obj


def _build_elevation_api_params(bbox_obj: BoundingBox, api_key: str) -> Dict[str, Any]:
    """Build OpenTopography query parameters from a normalized bbox."""
    return {
        "demtype": "AW3D30",
        "west": bbox_obj.west,
        "south": bbox_obj.south,
        "east": bbox_obj.east,
        "north": bbox_obj.north,
        "outputFormat": "GTiff",
        "API_Key": api_key,
    }


def _download_elevation_raster(
    params: Dict[str, Any],
) -> tuple[np.ndarray, rasterio.Affine, float, float]:
    """Download DEM data and return elevation array, transform, max and min."""
    url = "https://portal.opentopography.org/API/globaldem"
    try:
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()
        log_info(logger, "Elevation data downloaded successfully.")
        with BytesIO(response.content) as file_obj:
            with rasterio.open(file_obj) as dataset:
                elevation = dataset.read(1)
                if dataset.nodata is not None:
                    elevation = np.where(elevation == dataset.nodata, np.nan, elevation)
                max_elevation = float(np.nanmax(elevation))
                min_elevation = float(np.nanmin(elevation))
                log_info(logger, f"Elevation min: {min_elevation} m, max: {max_elevation} m")
                return elevation, dataset.transform, max_elevation, min_elevation
    except Exception as exc:
        log_error(logger, f"Failed to fetch elevation data: {exc}")
        raise


def fetch_elevation_from_api(bounds: Any) -> tuple[np.ndarray, float, float]:
    """Fetch elevation data for bounds and return DEM array with max/min values."""
    elevation, _transform, max_elevation, min_elevation = load_elevation_raster(bounds)
    return elevation, max_elevation, min_elevation


def load_elevation_raster(bounds: Any) -> tuple[np.ndarray, rasterio.Affine, float, float]:
    """Load DEM raster for bounds and return elevation, transform, max and min values."""
    api_key = os.getenv(_PROGRAM_CONFIG.providers.opentopo_api_key_env_var)
    log_info(logger, f"Using OpenTopography API Key: {_mask_api_key(api_key)}") # type: ignore
    bbox_obj = _normalize_bbox_for_api(bounds)
    params = _build_elevation_api_params(bbox_obj, api_key) # type: ignore

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[tuple[np.ndarray, rasterio.Affine, float, float]]()
    cache_key = cache_manager.build_key(
        {
            "demtype": params.get("demtype"),
            "west": params.get("west"),
            "south": params.get("south"),
            "east": params.get("east"),
            "north": params.get("north"),
            "outputFormat": params.get("outputFormat"),
        },
        provider="opentopography",
        algorithm_version=_ELEVATION_CACHE_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="elevation_raster",
    )
    cached = cache_manager.get(namespace=_ELEVATION_CACHE_NAMESPACE, key=cache_key, serializer=serializer)
    if cached is not None:
        log_info(logger, "Loaded elevation raster from cache.")
        return cached[0]

    raster = _download_elevation_raster(params)
    cache_manager.put(
        namespace=_ELEVATION_CACHE_NAMESPACE,
        key=cache_key,
        value=raster,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="elevation_raster",
            provider="opentopography",
            algorithm_version=_ELEVATION_CACHE_ALGORITHM_VERSION,
            format_version="1",
            extra={"demtype": str(params.get("demtype", ""))},
        ),
    )
    return raster


def sample_elevation_at_coords(
    lon: np.ndarray,
    lat: np.ndarray,
    elevation: np.ndarray,
    transform: rasterio.Affine,
) -> np.ndarray:
    """Sample elevation values from a DEM raster for longitude/latitude points."""
    lon_arr = np.asarray(lon, dtype=float)
    lat_arr = np.asarray(lat, dtype=float)
    rows, cols = rowcol(transform, lon_arr, lat_arr, op=round, precision=0)
    rows = np.asarray(rows, dtype=int)
    cols = np.asarray(cols, dtype=int)
    sampled = np.full(lon_arr.shape, np.nan, dtype=float)
    valid = (
        (rows >= 0)
        & (rows < elevation.shape[0])
        & (cols >= 0)
        & (cols < elevation.shape[1])
    )
    sampled[valid] = elevation[rows[valid], cols[valid]]
    return np.nan_to_num(sampled, nan=0.0)
