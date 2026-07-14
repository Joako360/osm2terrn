"""Generic bounding-box and world-size geometry utilities."""

from __future__ import annotations

from typing import Any, Tuple

import geopandas as gpd
import numpy as np
from pyproj import Transformer
from shapely.geometry import box

from osm2terrn.utils.geometry.crs import utm_crs_from_lonlat


def _coerce_bounds_geodataframe(bounds_like: Any) -> gpd.GeoDataFrame:
    """Normalize supported bounds-like inputs to a one-geometry GeoDataFrame."""
    if isinstance(bounds_like, gpd.GeoDataFrame):
        return bounds_like

    if hasattr(bounds_like, "total_bounds"):
        minx, miny, maxx, maxy = map(float, getattr(bounds_like, "total_bounds"))
        crs = getattr(bounds_like, "crs", None) or "EPSG:4326"
        return gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs=crs)

    bounds = getattr(bounds_like, "bounds", None)
    if isinstance(bounds, (tuple, list)) and len(bounds) == 4:
        minx, miny, maxx, maxy = map(float, bounds)
        crs = getattr(bounds_like, "crs", None) or "EPSG:4326"
        return gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs=crs)

    if all(hasattr(bounds_like, attribute) for attribute in ("min_x", "min_y", "max_x", "max_y")):
        minx = float(getattr(bounds_like, "min_x"))
        miny = float(getattr(bounds_like, "min_y"))
        maxx = float(getattr(bounds_like, "max_x"))
        maxy = float(getattr(bounds_like, "max_y"))
        crs = getattr(bounds_like, "crs", None) or "EPSG:4326"
        return gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs=crs)

    if all(hasattr(bounds_like, attribute) for attribute in ("west", "south", "east", "north")):
        west = float(getattr(bounds_like, "west"))
        south = float(getattr(bounds_like, "south"))
        east = float(getattr(bounds_like, "east"))
        north = float(getattr(bounds_like, "north"))
        crs = getattr(bounds_like, "crs", None) or "EPSG:4326"
        return gpd.GeoDataFrame(geometry=[box(west, south, east, north)], crs=crs)

    raise ValueError("Unsupported bounds format")


def bbox_size_meters(bounds_wgs84: Any) -> Tuple[float, float]:
    """Compute width and height in meters for a single-geometry bounds GeoDataFrame."""
    if bounds_wgs84 is None:
        raise ValueError("Bounds GeoDataFrame is None")
    bounds_frame = _coerce_bounds_geodataframe(bounds_wgs84)
    if bounds_frame.empty:
        raise ValueError("Bounds GeoDataFrame is empty")

    bounds_with_crs = bounds_frame
    if bounds_with_crs.crs is None:
        bounds_with_crs = bounds_with_crs.set_crs("EPSG:4326", allow_override=True)

    bounds_4326 = bounds_with_crs.to_crs("EPSG:4326")
    geometry = bounds_4326.geometry.iloc[0]
    if geometry is None or geometry.is_empty:
        raise ValueError("Bounds geometry is empty or invalid")

    centroid = geometry.centroid
    if centroid is None or centroid.is_empty:
        raise ValueError("Could not compute centroid for bounds")

    utm = utm_crs_from_lonlat(float(centroid.x), float(centroid.y))
    bounds_utm = bounds_with_crs.to_crs(utm)
    minx, miny, maxx, maxy = bounds_utm.total_bounds
    return float(maxx - minx), float(maxy - miny)


def _next_power_of_two(x: float, minimum: int = 1024, maximum: int = 1 << 15) -> int:
    """Return the next power-of-two integer greater than or equal to x."""
    if x <= minimum:
        return int(minimum)

    value = 1
    while value < x:
        value <<= 1
    return int(min(max(value, minimum), maximum))


def compute_world_params(
    bounds_wgs84: Any,
    page_size: int = 1025,
    snap_to_pow2: bool = True,
) -> Tuple[int, float]:
    """Compute square world size in meters and meters-per-pixel for the provided bounds."""
    width_m, height_m = bbox_size_meters(bounds_wgs84)
    side = max(width_m, height_m)
    world_size = _next_power_of_two(side) if snap_to_pow2 else int(np.ceil(side))
    meters_per_pixel = float(world_size) / float(max(page_size - 1, 1))
    return int(world_size), meters_per_pixel


def make_square_bounds_centered(bounds_wgs84: Any, side_meters: float) -> gpd.GeoDataFrame:
    """Build a square bounds in WGS84 centered on the input bounds centroid."""
    if bounds_wgs84 is None:
        raise ValueError("Bounds GeoDataFrame is None")
    bounds_frame = _coerce_bounds_geodataframe(bounds_wgs84)
    if bounds_frame.empty:
        raise ValueError("Bounds GeoDataFrame is empty")

    bounds_with_crs = bounds_frame
    if bounds_with_crs.crs is None:
        bounds_with_crs = bounds_with_crs.set_crs("EPSG:4326", allow_override=True)

    bounds_4326 = bounds_with_crs.to_crs("EPSG:4326")
    geometry = bounds_4326.geometry.iloc[0]
    if geometry is None or geometry.is_empty:
        raise ValueError("Bounds geometry is empty or invalid")

    centroid = geometry.centroid
    if centroid is None or centroid.is_empty:
        raise ValueError("Could not compute centroid for bounds")

    lon = float(centroid.x)
    lat = float(centroid.y)
    utm = utm_crs_from_lonlat(lon, lat)

    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    to_wgs84 = Transformer.from_crs(utm, "EPSG:4326", always_xy=True)

    half_side = float(side_meters) / 2.0
    x0, y0 = to_utm.transform(lon, lat)
    square_utm = box(x0 - half_side, y0 - half_side, x0 + half_side, y0 + half_side)

    min_lon, min_lat = to_wgs84.transform(square_utm.bounds[0], square_utm.bounds[1])
    max_lon, max_lat = to_wgs84.transform(square_utm.bounds[2], square_utm.bounds[3])
    return gpd.GeoDataFrame(geometry=[box(min_lon, min_lat, max_lon, max_lat)], crs="EPSG:4326")
