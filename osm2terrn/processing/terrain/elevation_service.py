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
from osm2terrn.domain.adapters.bounds import require_domain_bounding_box
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_error, log_info, log_warning

logger = get_logger("elevation_service")
_PROGRAM_CONFIG = get_program_config()
_ELEVATION_CACHE_NAMESPACE = "providers/elevation/raster"
_ELEVATION_CACHE_ALGORITHM_VERSION = "1"


def _normalize_bbox_for_api(bounds: BoundingBox) -> BoundingBox:
    """Return an EPSG:4326 bbox required by the OpenTopography API adapter."""
    bbox_obj = require_domain_bounding_box(bounds)
    if bbox_obj.crs and bbox_obj.crs != "EPSG:4326":
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
    failure_message = "Failed to fetch elevation data."
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
    except requests.HTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        detail = f"HTTP {status_code}" if status_code is not None else "HTTP request error"
        failure_message = f"Failed to fetch elevation data ({detail})."
    except Exception as exc:
        failure_message = f"Failed to fetch elevation data ({type(exc).__name__})."

    log_error(logger, failure_message)
    raise RuntimeError(failure_message)


def fetch_elevation_from_api(bounds: BoundingBox) -> tuple[np.ndarray, float, float]:
    """Fetch elevation data for bounds and return DEM array with max/min values."""
    elevation, _transform, max_elevation, min_elevation = load_elevation_raster(bounds)
    return elevation, max_elevation, min_elevation


def load_elevation_raster(bounds: BoundingBox) -> tuple[np.ndarray, rasterio.Affine, float, float]:
    """Load DEM raster for bounds and return elevation, transform, max and min values."""
    api_key = os.getenv(_PROGRAM_CONFIG.providers.opentopo_api_key_env_var)
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
