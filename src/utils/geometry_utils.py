import math
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, transform as shp_transform
from pyproj import Transformer, CRS
from geopandas import GeoDataFrame
from typing import Tuple
from shapely.geometry import box as shp_box

def utm_crs_from_lonlat(lon: float, lat: float) -> CRS:
    zone = int((lon + 180.0) // 6.0) + 1
    epsg = (32600 if lat >= 0.0 else 32700) + zone
    return CRS.from_epsg(epsg)

def densify_linestring(ls: LineString, step: float) -> LineString:
    if not isinstance(ls, LineString):
        raise ValueError("Input must be a LineString")
    if step <= 0:
        raise ValueError("Step must be positive")
    if ls.length <= step:
        return ls
    n = int(np.ceil(ls.length / step))
    dists = np.linspace(0, ls.length, n + 1)
    pts = [ls.interpolate(d) for d in dists]
    return LineString([(p.x, p.y) for p in pts])

def densify_preserve_vertices(ls: LineString, step: float) -> LineString:
    if ls.length <= step:
        return ls
    new_coords = [ls.coords[0]]
    for i in range(len(ls.coords) - 1):
        p0 = ls.coords[i]
        p1 = ls.coords[i + 1]
        seg = LineString([p0, p1])
        seg_len = seg.length
        if seg_len > step:
            num_points = int(np.floor(seg_len / step))
            for j in range(1, num_points + 1):
                d = j * step
                if d < seg_len:
                    pt = seg.interpolate(d)
                    new_coords.append((pt.x, pt.y))
        new_coords.append(p1)
    return LineString(new_coords)

def densify_adaptive_by_curvature(ls: LineString, min_step: float, max_step: float, preserve_ends: bool = True) -> LineString:
    if not isinstance(ls, LineString):
        return ls
    if ls.length <= min_step:
        return ls
    coords = np.asarray(ls.coords, dtype=float)
    if coords.shape[0] < 3:
        mid = 0.5 * (min_step + max_step)
        return densify_linestring(ls, step=mid)
    def heading(a, b) -> float:
        return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    headings = []
    for i in range(len(coords) - 1):
        headings.append(heading(coords[i], coords[i + 1]))
    headings = np.array(headings)
    angle_changes = [0.0]
    for i in range(1, len(headings)):
        d = abs((headings[i] - headings[i - 1] + 180.0) % 360.0 - 180.0)
        angle_changes.append(float(d))
    angle_changes.append(0.0)
    angle_changes = np.array(angle_changes)
    norm = np.clip(angle_changes / 180.0, 0.0, 1.0)
    if len(norm) >= 5:
        kernel = np.ones(5) / 5.0
        norm = np.convolve(norm, kernel, mode="same")
    step_per_vertex = max_step - (max_step - min_step) * norm
    out_pts = []
    if preserve_ends:
        out_pts.append((coords[0, 0], coords[0, 1]))
    dist = 0.0
    total = float(ls.length)
    cumlen = [0.0]
    acc = 0.0
    for i in range(len(coords) - 1):
        seg = LineString([tuple(coords[i]), tuple(coords[i + 1])])
        acc += float(seg.length)
        cumlen.append(acc)
    cumlen = np.array(cumlen)
    def step_at(s: float) -> float:
        idx = int(np.searchsorted(cumlen, s, side="right") - 1)
        idx = np.clip(idx, 0, len(step_per_vertex) - 1)
        return float(step_per_vertex[idx])
    while dist < total:
        step_here = max(min_step, min(max_step, step_at(dist)))
        dist = min(total, dist + step_here)
        pt = ls.interpolate(dist)
        out_pts.append((pt.x, pt.y))
    if preserve_ends:
        out_pts[-1] = (coords[-1, 0], coords[-1, 1])
    clean = []
    last = None
    for xy in out_pts:
        if last is None or (abs(xy[0] - last[0]) > 1e-9 or abs(xy[1] - last[1]) > 1e-9):
            clean.append(xy)
            last = xy
    return LineString(clean)

def densify_by_max_segment_length(ls: LineString, max_len: float) -> LineString:
    if not isinstance(ls, LineString):
        return ls
    coords = list(ls.coords)
    if len(coords) < 2:
        return ls
    first = coords[0]
    new_coords = [(float(first[0]), float(first[1]))]
    for i in range(len(coords) - 1):
        p0 = np.array(coords[i][:2], dtype=float)
        p1 = np.array(coords[i + 1][:2], dtype=float)
        seg_vec = p1 - p0
        seg_len = float(np.linalg.norm(seg_vec))
        if seg_len > max_len and seg_len > 0:
            n_add = int(math.floor(seg_len / max_len))
            for j in range(1, n_add + 1):
                t = (j * max_len) / seg_len
                if t < 1.0:
                    p = p0 + t * seg_vec
                    new_coords.append((float(p[0]), float(p[1])))
        new_coords.append((float(p1[0]), float(p1[1])))
    dedup = []
    last = None
    for xy in new_coords:
        if last is None or (abs(xy[0] - last[0]) > 1e-9 or abs(xy[1] - last[1]) > 1e-9):
            dedup.append(xy)
            last = xy
    return LineString(dedup)

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
    if bounds_wgs84 is None or bounds_wgs84.empty:
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
    if bounds_wgs84 is None or bounds_wgs84.empty:
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
