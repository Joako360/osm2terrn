from typing import Any, Dict, Optional

import numpy as np
import scipy.ndimage
from PIL import Image

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.config.settings import get_program_config
from osm2terrn.processing.terrain.elevation_service import fetch_elevation_from_api
from osm2terrn.processing.terrain.terrain_colormap_ops import render_heightmap_rgb
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.utils.logger import get_logger, log_error, log_info, log_warning
from osm2terrn.tools.visualization.heightmaps import plot_heightmap

logger = get_logger("heightmap_handler")
_PROGRAM_CONFIG = get_program_config()
_HEIGHTMAP_SMOOTH_CACHE_NAMESPACE = "processing/terrain/heightmap-smoothed"
_HEIGHTMAP_SMOOTH_ALGORITHM_VERSION = "1"


def _normalize_elevation(
    elevation: np.ndarray,
    min_elevation: float,
    max_elevation: float,
) -> np.ndarray:
    """Normalize DEM values to [0, 1], handling NaNs and flat areas safely."""
    elevation = np.asarray(elevation, dtype=float)
    elevation_range = float(max_elevation - min_elevation)
    if elevation_range <= 0:
        return np.zeros_like(elevation, dtype=float)
    normalized = (elevation - float(min_elevation)) / elevation_range
    return np.nan_to_num(normalized, nan=0.0)


def _build_flat_elevation(output_size: tuple[int, int]) -> tuple[np.ndarray, float, float]:
    """Return a flat fallback elevation map with zero stats."""
    width, height = output_size
    return np.zeros((height, width), dtype=np.float32), 0.0, 0.0


def _prepare_elevation_data(
    bounds: Any,
    elevation_data: Optional[dict],
    output_size: tuple[int, int],
) -> tuple[np.ndarray, float, float]:
    """Load or build elevation values, then normalize them for image generation."""
    try:
        bbox_obj = BoundingBox(bounds)
    except Exception as exc:
        raise ValueError(f"Invalid bounds: {exc}") from exc

    if elevation_data and {"elevation", "maxh", "minh"}.issubset(elevation_data):
        elevation = elevation_data["elevation"]
        maxh = elevation_data["maxh"]
        minh = elevation_data["minh"]
        return _normalize_elevation(elevation, minh, maxh), maxh, minh

    try:
        elevation, maxh, minh = fetch_elevation_from_api(bbox_obj)
        return _normalize_elevation(elevation, minh, maxh), maxh, minh
    except Exception as exc:
        log_warning(logger, f"Falling back to flat heightmap due to elevation fetch failure: {exc}")
        return _build_flat_elevation(output_size)


def _save_map_image(
    elevation_smoothed: np.ndarray,
    output_size: tuple[int, int],
    output_path: str,
    image_mode: str = "L",
    cmap_name: Optional[str] = None,
    log_label: str = "Image",
) -> None:
    """Persist a resized elevation-derived image (grayscale or colormapped RGB)."""
    if image_mode == "RGB":
        if not cmap_name:
            raise ValueError("cmap_name is required when image_mode is RGB.")
        image_data = render_heightmap_rgb(elevation_smoothed, cmap_name)
    else:
        image_data = (elevation_smoothed * 255).astype(np.uint8)

    image = Image.fromarray(image_data, mode=image_mode)
    image = image.resize(output_size, Image.Resampling.LANCZOS)
    image.save(output_path)
    log_info(logger, f"{log_label} saved to: {output_path}")


def plot_elevation_map(
    elevation: np.ndarray,
    cmap: str = "gray",
    vmin: float = 0.0,
    vmax: float = 1.0,
) -> None:
    """Display an elevation map using the shared visualization utility."""
    if elevation.size == 0:
        log_error(logger, "Elevation array is empty. Skipping plot.")
        return

    plot_heightmap(
        elevation,
        title="Elevation Map",
        cmap_name=cmap,
        vmin=vmin,
        vmax=vmax,
    )
    log_info(logger, "Elevation map displayed.")


def generate_heightmap_n_texture(
    bounds: Any,
    heightmap_path: str = "heightmap.png",
    groundmap_path: str = "groundmap.png",
    cmap_name: str = _PROGRAM_CONFIG.terrain_runtime.default_colormap,
    output_size: tuple[int, int] = _PROGRAM_CONFIG.terrain_runtime.output_size,
    smoothing_sigma: float = _PROGRAM_CONFIG.terrain_runtime.smoothing_sigma,
    elevation_data: Optional[dict] = None,
) -> Optional[Dict[str, float]]:
    """
    Generate and save both grayscale heightmap and colored ground texture.

    Returns elevation statistics, or None if bounds are invalid.
    """
    try:
        elevation_normalized, maxh, minh = _prepare_elevation_data(
            bounds=bounds,
            elevation_data=elevation_data,
            output_size=output_size,
        )
    except ValueError as exc:
        log_warning(logger, f"No valid bbox provided: {exc}")
        return None

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[np.ndarray]()
    elevation_smoothed: np.ndarray
    if elevation_data is None:
        bbox_obj = BoundingBox(bounds)
        cache_key = cache_manager.build_key(
            {
                "bbox": list(bbox_obj.to_tuple()),
                "bbox_crs": str(getattr(bbox_obj, "crs", "") or ""),
                "bbox_is_projected": bool(getattr(bbox_obj, "is_projected", False)),
                "output_size": [int(output_size[0]), int(output_size[1])],
                "smoothing_sigma": float(smoothing_sigma),
            },
            provider="terrain",
            algorithm_version=_HEIGHTMAP_SMOOTH_ALGORITHM_VERSION,
            format_version="1",
            artifact_type="heightmap_smoothed",
        )
        cached = cache_manager.get(
            namespace=_HEIGHTMAP_SMOOTH_CACHE_NAMESPACE,
            key=cache_key,
            serializer=serializer,
        )
        if cached is not None:
            elevation_smoothed = cached[0]
        else:
            elevation_smoothed = scipy.ndimage.gaussian_filter(elevation_normalized, sigma=smoothing_sigma)
            cache_manager.put(
                namespace=_HEIGHTMAP_SMOOTH_CACHE_NAMESPACE,
                key=cache_key,
                value=elevation_smoothed,
                serializer=serializer,
                metadata=CacheMetadata(
                    artifact_type="heightmap_smoothed",
                    provider="terrain",
                    algorithm_version=_HEIGHTMAP_SMOOTH_ALGORITHM_VERSION,
                    format_version="1",
                    extra={"sigma": float(smoothing_sigma)},
                ),
            )
    else:
        elevation_smoothed = scipy.ndimage.gaussian_filter(elevation_normalized, sigma=smoothing_sigma)

    _save_map_image(
        elevation_smoothed=elevation_smoothed,
        output_size=output_size,
        output_path=heightmap_path,
        image_mode="L",
        log_label="Heightmap",
    )
    _save_map_image(
        elevation_smoothed=elevation_smoothed,
        output_size=output_size,
        output_path=groundmap_path,
        image_mode="RGB",
        cmap_name=cmap_name,
        log_label="Ground texture",
    )

    return {
        "min_elevation": float(minh),
        "max_elevation": float(maxh),
        "elevation_range": float(maxh - minh),
    }
