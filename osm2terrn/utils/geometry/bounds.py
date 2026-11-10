"""Generic bounding-box and world-size geometry utilities."""

from __future__ import annotations

from typing import Any, Tuple

import numpy as np
from pyproj import Transformer

from osm2terrn.domain.adapters.bounds import require_domain_bounding_box
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.utils.geometry.crs import utm_crs_from_lonlat


def _as_wgs84_bbox(bounds: BoundingBox) -> BoundingBox:
    """Return bounds expressed in EPSG:4326 for geodesic-safe projections."""
    if bounds.crs is None or bounds.crs == "EPSG:4326":
        return BoundingBox(bounds, crs="EPSG:4326", is_projected=False)
    to_wgs84 = Transformer.from_crs(bounds.crs, "EPSG:4326", always_xy=True)
    corners = (
        (bounds.min_x, bounds.min_y),
        (bounds.min_x, bounds.max_y),
        (bounds.max_x, bounds.min_y),
        (bounds.max_x, bounds.max_y),
    )
    transformed = [to_wgs84.transform(x, y) for x, y in corners]
    xs = [float(point[0]) for point in transformed]
    ys = [float(point[1]) for point in transformed]
    return BoundingBox(
        min(xs),
        min(ys),
        max(xs),
        max(ys),
        crs="EPSG:4326",
        is_projected=False,
    )


def bbox_size_meters(bounds: Any) -> Tuple[float, float]:
    """Compute width and height in meters for supported bounds-like inputs."""
    if hasattr(bounds, "empty") and bool(getattr(bounds, "empty")):
        raise ValueError("Bounds GeoDataFrame is empty")

    bbox = require_domain_bounding_box(bounds)

    if getattr(bbox, "is_projected", False):
        return float(bbox.width), float(bbox.height)

    bounds_4326 = _as_wgs84_bbox(bbox)
    center = bounds_4326.center
    utm = utm_crs_from_lonlat(float(center.x), float(center.y))
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)

    corners = (
        (bounds_4326.min_x, bounds_4326.min_y),
        (bounds_4326.min_x, bounds_4326.max_y),
        (bounds_4326.max_x, bounds_4326.min_y),
        (bounds_4326.max_x, bounds_4326.max_y),
    )
    transformed = [to_utm.transform(x, y) for x, y in corners]
    xs = [float(point[0]) for point in transformed]
    ys = [float(point[1]) for point in transformed]
    return float(max(xs) - min(xs)), float(max(ys) - min(ys))


def _next_power_of_two(x: float, minimum: int = 1024, maximum: int = 1 << 15) -> int:
    """Return the next power-of-two integer greater than or equal to x."""
    if x <= minimum:
        return int(minimum)

    value = 1
    while value < x:
        value <<= 1
    return int(min(max(value, minimum), maximum))


def compute_world_params(
    bounds: Any,
    page_size: int = 1025,
    snap_to_pow2: bool = True,
) -> Tuple[int, float]:
    """Compute square world size in meters and meters-per-pixel for the provided bounds."""
    width_m, height_m = bbox_size_meters(bounds)
    side = max(width_m, height_m)
    world_size = _next_power_of_two(side) if snap_to_pow2 else int(np.ceil(side))
    meters_per_pixel = float(world_size) / float(max(page_size - 1, 1))
    return int(world_size), meters_per_pixel


def make_square_bounds_centered(bounds: Any, side_meters: float) -> BoundingBox:
    """Build a square BoundingBox centered on the input bounds centroid."""
    bbox = require_domain_bounding_box(bounds)

    if getattr(bbox, "is_projected", False):
        center = bbox.center
        half_side = float(side_meters) / 2.0
        return BoundingBox(
            center.x - half_side,
            center.y - half_side,
            center.x + half_side,
            center.y + half_side,
            crs=bbox.crs,
            is_projected=True,
        )

    bounds_4326 = _as_wgs84_bbox(bbox)
    center = bounds_4326.center
    lon = float(center.x)
    lat = float(center.y)

    utm = utm_crs_from_lonlat(lon, lat)
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    to_wgs84 = Transformer.from_crs(utm, "EPSG:4326", always_xy=True)

    x0, y0 = to_utm.transform(lon, lat)
    half_side = float(side_meters) / 2.0
    min_lon, min_lat = to_wgs84.transform(x0 - half_side, y0 - half_side)
    max_lon, max_lat = to_wgs84.transform(x0 + half_side, y0 + half_side)

    return BoundingBox(
        float(min_lon),
        float(min_lat),
        float(max_lon),
        float(max_lat),
        crs="EPSG:4326",
        is_projected=False,
    )
