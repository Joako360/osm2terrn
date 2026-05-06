import math
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, transform as shp_transform
from pyproj import Transformer, CRS
from geopandas import GeoDataFrame
from typing import Tuple
from shapely.geometry import box as shp_box
from utils.bbox import BBox

def utm_crs_from_lonlat(lon: float, lat: float) -> CRS:
    zone = int((lon + 180.0) // 6.0) + 1
    epsg = (32600 if lat >= 0.0 else 32700) + zone
    return CRS.from_epsg(epsg)

def to_local_coords(xs, ys, lon0, lat0):
    utm = utm_crs_from_lonlat(lon0, lat0)
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    x0, y0 = to_utm.transform(lon0, lat0)
    X, Y = to_utm.transform(xs, ys)
    return list(zip(np.array(X) - x0, np.array(Y) - y0))


def bbox_size_meters(bounds_wgs84: GeoDataFrame) -> Tuple[float, float]:
    """
    Compute bbox width/height in meters by projecting to the local UTM zone
    determined from the bbox centroid.
    """
    # Accept either a GeoDataFrame or a BBox instance for convenience
    if bounds_wgs84 is None:
        raise ValueError("Bounds GeoDataFrame or BBox is None")
    if isinstance(bounds_wgs84, BBox):
        # If the BBox is already in projected units (meters), we can compute size directly
        if getattr(bounds_wgs84, "is_projected", False):
            width = float(bounds_wgs84.east - bounds_wgs84.west)
            height = float(bounds_wgs84.north - bounds_wgs84.south)
            return width, height
        # otherwise create a GeoDataFrame from the BBox; use provided CRS when available
        crs = bounds_wgs84.crs if bounds_wgs84.crs is not None else "EPSG:4326"
        gdf = GeoDataFrame(geometry=[bounds_wgs84.to_shapely()], crs=crs)
        bounds_wgs84 = gdf
    if bounds_wgs84.empty:
        raise ValueError("Bounds GeoDataFrame is empty")
    # Determine centroid in lon/lat
    b4326 = bounds_wgs84.to_crs(4326)
    cx = float(b4326.geometry.centroid.x.iloc[0])
    cy = float(b4326.geometry.centroid.y.iloc[0])
    utm = utm_crs_from_lonlat(cx, cy)
    b_utm = bounds_wgs84.to_crs(utm)
    minx, miny, maxx, maxy = b_utm.total_bounds
    return float(maxx - minx), float(maxy - miny)


def _next_power_of_two(x: float, minimum: int = 1024, maximum: int = 1 << 15) -> int:
    """
    Return the next power-of-two integer >= x, clamped to [minimum, maximum].
    """
    if x <= minimum:
        return int(minimum)
    n = 1
    while n < x:
        n <<= 1
    return int(min(max(n, minimum), maximum))


def compute_world_params(
    bounds_wgs84: GeoDataFrame,
    page_size: int = 1025,
    snap_to_pow2: bool = True,
) -> Tuple[int, float]:
    """
    Given geographic bounds (EPSG:4326), compute a square world size (meters)
    and meters-per-pixel for a square heightmap of given page_size (2^n+1).

    - If snap_to_pow2 is True, world size is ceil to next power of two (meters).
    - Otherwise, uses the exact max(width_m, height_m) rounded to int.

    Returns: (world_size_meters, meters_per_pixel)
    """
    w_m, h_m = bbox_size_meters(bounds_wgs84)
    side = max(w_m, h_m)
    world_size = _next_power_of_two(side) if snap_to_pow2 else int(np.ceil(side))
    meters_per_pixel = float(world_size) / float(max(page_size - 1, 1))
    return int(world_size), meters_per_pixel


def make_square_bounds_centered(bounds_wgs84: GeoDataFrame, side_meters: float) -> GeoDataFrame:
    """
    Return a square bounds GeoDataFrame in WGS84 centered on the original bbox centroid,
    with side length = side_meters. Uses UTM projection to build a metric square and reprojects back.
    """
    if bounds_wgs84 is None:
        raise ValueError("Bounds GeoDataFrame or BBox is None")
    # allow BBox inputs for convenience
    if isinstance(bounds_wgs84, BBox):
        crs = bounds_wgs84.crs if bounds_wgs84.crs is not None else "EPSG:4326"
        bounds_wgs84 = GeoDataFrame(geometry=[bounds_wgs84.to_shapely()], crs=crs)
    if bounds_wgs84.empty:
        raise ValueError("Bounds GeoDataFrame is empty")
    b4326 = bounds_wgs84.to_crs(4326)
    cx = float(b4326.geometry.centroid.x.iloc[0])
    cy = float(b4326.geometry.centroid.y.iloc[0])
    utm = utm_crs_from_lonlat(cx, cy)
    half = float(side_meters) / 2.0
    # Create a small square around centroid in UTM
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    to_wgs = Transformer.from_crs(utm, "EPSG:4326", always_xy=True)
    x0, y0 = to_utm.transform(cx, cy)
    square_utm = shp_box(x0 - half, y0 - half, x0 + half, y0 + half)
    # Transform back to WGS84 coordinates
    minx, miny = to_wgs.transform(square_utm.bounds[0], square_utm.bounds[1])
    maxx, maxy = to_wgs.transform(square_utm.bounds[2], square_utm.bounds[3])
    return GeoDataFrame(geometry=[shp_box(minx, miny, maxx, maxy)], crs="EPSG:4326")
