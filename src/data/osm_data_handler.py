from collections import OrderedDict
import geopandas as gpd
import fused 
import osmnx as ox
from typing import Dict, Tuple
from shapely.geometry import box as shp_box, Point as ShpPoint, Polygon as ShpPolygon, MultiPolygon as ShpMultiPolygon
from utils.constants import Colors, custom_tags, map_geometries, networks
from utils.geometry import transform_gdf, transform_graph
from utils.logger import get_logger, log_error, log_info
import re
import requests
import os

logger = get_logger("osm_data_handler")

ox.settings.elevation_url_template = 'https://api.opentopodata.org/v1/test-dataset?locations={locations}' # type: ignore
ox.settings.log_console = True # type: ignore
ox.settings.useful_tags_way = ox.settings.useful_tags_way + custom_tags # type: ignore
# Reduce query size to encourage osmnx to split large areas into smaller Overpass queries
try:
    ox.settings.max_query_area_size = 25_000_000  # type: ignore
except Exception:
    pass
# Tweak request timeout to fail faster on unresponsive endpoints
try:
    ox.settings.requests_timeout = int(os.environ.get('OSM2TERRN_REQUESTS_TIMEOUT', '120'))  # type: ignore
except Exception:
    pass
# Allow users to override overpass rate limiting (default True = be nice)
try:
    _orl = os.environ.get('OSM2TERRN_OVERPASS_RATE_LIMIT')
    if _orl is not None:
        ox.settings.overpass_rate_limit = (_orl.strip().lower() in {'1','true','yes'})  # type: ignore
except Exception:
    pass
ox.__version__
# Example: custom_filter='["railway"~"tram|rail"]'
# Download graph from OSM with osmnx parameters: place query, which option and optional custom filters


def _overpass_status_wait_seconds(base_url: str, timeout: float = 5.0) -> float:
    """
    Query Overpass /status endpoint and estimate wait time in seconds.

    Returns 0 if slots are available or status cannot be parsed (optimistic).
    """
    try:
        url = base_url.rstrip('/') + '/status'
        resp = requests.get(url, timeout=timeout)
        txt = resp.text.lower()
        # Common patterns
        if 'slots available now' in txt or 'available now' in txt:
            return 0.0
        # in about N seconds
        m = re.search(r'in about\s+(\d+)\s+seconds', txt)
        if m:
            return float(m.group(1))
        # Slot available after: HH:MM:SS
        m = re.search(r'slot available after:?\s*(\d{1,2}):(\d{2}):(\d{2})', txt)
        if m:
            h, mi, s = map(int, m.groups())
            return float(h * 3600 + mi * 60 + s)
        # Slot available after: N seconds
        m = re.search(r'slot available after:?\s*(\d+)\s*seconds', txt)
        if m:
            return float(m.group(1))
    except Exception:
        # If status fails, assume it's fine to try
        return 0.0
    return 0.0


def pick_fast_overpass(threshold_seconds: float = 60.0) -> str:
    """
    Choose an Overpass API mirror with the shortest expected wait, set it in osmnx settings,
    and return the selected base URL. Honors the env var OSM2TERRN_OVERPASS_URL if provided.
    """
    import os
    env_url = os.environ.get('OSM2TERRN_OVERPASS_URL')
    if env_url:
        ox.settings.overpass_url = env_url  # type: ignore
        log_info(logger, f"Using Overpass URL from env: {env_url}")
        return env_url
    # Candidate mirrors (order by general reliability)
    candidates = [
        'https://overpass-api.de/api',
        'https://lz4.overpass-api.de/api',
        'https://overpass.kumi.systems/api',
        'https://overpass.openstreetmap.fr/api',
    ]
    best_url = candidates[0]
    best_wait = float('inf')
    for url in candidates:
        wait = _overpass_status_wait_seconds(url)
        if wait < best_wait:
            best_wait = wait
            best_url = url
    ox.settings.overpass_url = best_url  # type: ignore
    if best_wait > threshold_seconds:
        log_info(logger, f"Selected Overpass mirror {best_url} but estimated wait is {best_wait:.0f}s. You can set OSM2TERRN_OVERPASS_URL to override.")
    else:
        log_info(logger, f"Selected Overpass mirror {best_url} (estimated wait {best_wait:.0f}s)")
    return best_url



def download_data_from_bbox(bbox: Tuple[float, float, float, float]) -> Dict:
    """
    Downloads and processes OSM data using a bounding box only.
    Args:
        bbox (Tuple): (west, south, east, north)
    Returns:
        Dict: Processed data (bounds, networks, geometries, etc.)
    """
    d = {}
    # Pick a responsive Overpass mirror before any requests
    try:
        pick_fast_overpass()
    except Exception:
        pass
    bounds_gdf = gpd.GeoDataFrame(geometry=[shp_box(*bbox)], crs="EPSG:4326")
    bounds_proj = bounds_gdf.to_crs(3857)
    centroid_geom = bounds_proj.geometry.centroid.iloc[0]
    if isinstance(centroid_geom, ShpPoint):
        x_0, y_0 = centroid_geom.x, centroid_geom.y
    else:
        log_error(logger, "Centroid is not a Point geometry. Defaulting to (0, 0).")
        x_0, y_0 = 0.0, 0.0
    d['bounds'] = bounds_gdf
    d['bounds_proj'] = bounds_proj
    d['x_0'] = x_0
    d['y_0'] = y_0
    polygon = shp_box(*bbox)
    # Optional filtering of geometry categories via env var
    geoms_env = os.environ.get('OSM2TERRN_GEOMETRIES')
    enabled_geoms = None
    if geoms_env:
        enabled_geoms = {s.strip() for s in geoms_env.split(',') if s.strip()}
        log_info(logger, f"Enabled geometries from env: {sorted(enabled_geoms)}")
    for typ, tag in map_geometries.items():
        if enabled_geoms is not None and typ not in enabled_geoms:
            continue
        try:
            gdf = ox.features_from_polygon(polygon, tag)
            d[typ] = transform_gdf(gdf, x_0, y_0) if gdf is not None and not gdf.empty else None
        except ValueError:
            d[typ] = None
    # Optional filtering of network categories via env var
    nets_env = os.environ.get('OSM2TERRN_NETWORKS', 'roads')
    enabled_nets = {s.strip() for s in nets_env.split(',') if s.strip()}
    log_info(logger, f"Enabled networks: {sorted(enabled_nets)}")
    for typ, cf in networks.items():
        if typ not in enabled_nets:
            continue
        try:
            # graph_from_bbox expects (north, south, east, west)
            north, south, east, west = bbox[3], bbox[1], bbox[2], bbox[0]
            G = ox.graph_from_bbox((north, south, east, west), network_type="drive_service", simplify=False, retain_all=True, custom_filter=cf)
            d[typ] = transform_graph(G, x_0, y_0) if G is not None and len(G.nodes) > 0 else None
        except Exception:
            d[typ] = None
    return d

# Ask for a place, makes a Nominatim query and prints the results in a table
# Returns a tuple of the place name and the index of the result chosen by the user



def download_menu() -> tuple[str, tuple[float, float, float, float]] | tuple[None, None]:
    """
    Shows a menu to choose between searching by city name or entering bounding box manually.
    Returns:
        Tuple of (place name, bounding box) or (None, None) if cancelled.
    """
    print("Select download mode:")
    print("1. Search by city name")
    print("2. Enter custom bounding box coordinates")
    mode = input("Enter option (1 or 2, or 0 to cancel): ").strip()
    if mode == "0":
        return None, None
    if mode == "2":
        print("Enter the limits of the custom bounding box.")
        print("Remember:")
        print("- West (xmin) < East (xmax)")
        print("- South (ymin) < North (ymax)")
        print("- Longitudes: -180 to 180")
        print("- Latitudes: -90 to 90")
        def get_float(prompt, minval, maxval):
            while True:
                try:
                    val = float(input(prompt))
                    if val < minval or val > maxval:
                        print(f"Value must be between {minval} and {maxval}.")
                        continue
                    return val
                except ValueError:
                    print("Invalid number. Please try again.")
        west = get_float("West (xmin, min longitude): ", -180, 180)
        south = get_float("South (ymin, min latitude): ", -90, 90)
        east = get_float("East (xmax, max longitude): ", -180, 180)
        north = get_float("North (ymax, max latitude): ", -90, 90)
        if west >= east or south >= north:
            print("Invalid bounding box: west must be < east and south < north.")
            return None, None
        bbox = (west, south, east, north)
        return "custom_bbox", bbox
    # Default: search by city name
    place = input(
        'Enter the city name (will be used as file name): ').title()
    if place == '0':
        return None, None
    nmntm_req = OrderedDict([('q', place), ('format', 'json')])
    nmntm_res = ox._nominatim._nominatim_request(nmntm_req) # type: ignore
    while not nmntm_res:
        print("No results. Hint: City may be OSM admin_level = 7+")
        place = input("Enter the city name (Enter 0 to exit): ").title()
        if place == '0':
            return None, None
        nmntm_req = OrderedDict([('q', place), ('format', 'json')])
        nmntm_res = ox._nominatim._nominatim_request(nmntm_req) # type: ignore
    print("{:<6}║{:<50}║{:<14}║{:<10}".format(
        'Option', 'Display name', 'Type', 'Class'))
    print('═' * 6 + '╬' + '═' * 50 + '╬' + '═' * 14 + '╬' + '═' * 10)
    for idx, result in enumerate(nmntm_res, start=1):
        result_line = "{:<6}║{:<50}║{:<14}║{:<10}".format(
            str(idx), result['display_name'][:50], result['type'][:14], result['class'][:10])
        if result['type'] == 'administrative' or result['class'] == 'boundary':
            print(Colors.bg_green + result_line + Colors.reset)
        elif result['osm_type'] != 'relation':
            print(Colors.bg_red + result_line + Colors.reset)
        else:
            print(result_line)
    while True:
        try:
            which = int(input("Which result? (Enter number): "))
            if 1 <= which <= len(nmntm_res):
                break
            print("Invalid option. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    selected = nmntm_res[which-1]
    bbox = (
        float(selected['boundingbox'][2]),  # west (min longitude)
        float(selected['boundingbox'][0]),  # south (min latitude)
        float(selected['boundingbox'][3]),  # east (max longitude)
        float(selected['boundingbox'][1])   # north (max latitude)
    )
    return place, bbox


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
    udf = fused.load("https://github.com/fusedio/udfs/tree/main/public/Overture_Maps_Example")
    param = {
        'bbox': bbox,
        'overture_type': 'building',
    }
    gdf_output = fused.run(udf, parameters=param) # type: ignore
    gdf = gpd.GeoDataFrame(gdf_output, geometry='geometry', crs='epsg:4326')
    # gdf.plot()
    return gdf