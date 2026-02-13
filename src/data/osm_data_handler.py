from collections import OrderedDict
import logging
import geopandas as gpd
import fused 
import osmnx as ox
from typing import Dict, Tuple
from shapely.geometry import box as shp_box, Point as ShpPoint
from utils.bbox import BBox
from utils.constants import Colors, custom_tags, map_geometries, networks
from utils.geometry import transform_gdf, transform_graph
from utils.logger import get_logger, log_error, log_info, log_warning
import os

logger = get_logger("osm_data_handler")

ox.settings.elevation_url_template = 'https://api.opentopodata.org/v1/test-dataset?locations={locations}' # type: ignore
ox.settings.log_console = True # type: ignore
ox.settings.log_file = True # type: ignore
ox.settings.log_level = logging.ERROR # type: ignore
ox.settings.useful_tags_way = ox.settings.useful_tags_way + custom_tags # type: ignore
# Reduce query size to encourage osmnx to split large areas into smaller Overpass queries
try:
    ox.settings.max_query_area_size = int(os.getenv('OVERPASS_MAX_QUERY_AREA_SIZE', 2_500_000_000))  # type: ignore
except Exception:
    pass
# Tweak request timeout to fail faster on unresponsive endpoints
try:
    ox.settings.requests_timeout = int(os.getenv('OVERPASS_REQUESTS_TIMEOUT', 1000))  # type: ignore
except Exception:
    pass
# Allow users to override overpass rate limiting (default True = be nice)
try:
    ox.settings.overpass_rate_limit = bool(os.getenv('OVERPASS_RATE_LIMIT', True))  # type: ignore
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

    # prefer BBox.to_shapely() to keep single parsing point
    polygon = use_bbox.to_shapely()
    west, south, east, north = use_bbox.to_tuple()
    # Find origin point in centroid
    # If bbox had an explicit CRS, use it; otherwise default to EPSG:4326
    gdf_crs = bbox_obj.crs if bbox_obj.crs is not None else "EPSG:4326"
    bounds_gdf = gpd.GeoDataFrame(geometry=[polygon], crs=gdf_crs)
    bounds_proj = bounds_gdf.to_crs(3857)
    centroid_geom = bounds_proj.geometry.centroid.iloc[0]
    try:
        x_0, y_0 = (centroid_geom.x, centroid_geom.y) # type: ignore
    except Exception:
        log_error(logger, "Could not compute centroid; defaulting origin to (0,0).")
        x_0, y_0 = 0.0, 0.0
    d['bounds'] = bounds_gdf.to_crs(4326)
    d['x_0'] = x_0
    d['y_0'] = y_0

    # Download simple geometries (use bbox-based query in lat/lon)
    # Note: osmnx expects (west, south, east, north)
    for typ, tag in map_geometries.items():
        try:
            # use bbox query in lat/lon (west, south, east, north)
            gdf = ox.features_from_bbox(west, south, east, north, tags=tag)  # type: ignore
            if gdf is None or gdf.empty:
                d[typ] = None
            else:
                d[typ] = transform_gdf(gdf, x_0, y_0)
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
                d[typ] = transform_graph(G, x_0, y_0)
        except Exception as exc:
            log_info(logger, f"Skipped network {typ} due to error: {exc}")
            d[typ] = None

    return d


# Download graph from OSM with osmnx parameters: place query, which option and optional custom filters
def download_menu() -> tuple[str, tuple[float, float, float, float]] | tuple[None, None]:
    """
    Shows a menu to choose between searching by city name or entering bounding box manually.
    Returns:
     - Option 2: enter bbox manually (validated for ranges).
     - Option 1: search by place name, show simple list of results, pick one.

    """
    print("Select download mode:")
    print("1. Search by place name")
    print("2. Enter custom bounding box")
    print("0. Cancel")
    mode = input("Enter option (0/1/2): ").strip()
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
        west = get_float("West (xmin, min longitude): ", -180., 180.)
        south = get_float("South (ymin, min latitude): ", -90., 90.)
        east = get_float("East (xmax, max longitude): ", -180., 180.)
        north = get_float("North (ymax, max latitude): ", -90., 90.)
        if west >= east or south >= north:
            print("Invalid bounding box: west must be < east and south < north.")
            return None, None
        bbox = (west, south, east, north)
        return "custom_bbox", bbox

    # Option 1: simple Nominatim search
    place = input("Enter the place name: ").strip()
    if not place:
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
        'Option', 
        'Display name', 
        'Type', 
        'Class'
        ))
    print('═' * 6 + '╬' + '═' * 50 + '╬' + '═' * 14 + '╬' + '═' * 10)
    for idx, result in enumerate(nmntm_res, start=1):
        result_line = "{:<6}║{:<50}║{:<14}║{:<10}".format(
            str(idx), 
            result['display_name'][:50], 
            result['type'][:14], 
            result['class'][:10]
            )
        if result['type'] == 'administrative' or result['class'] == 'boundary':
            print(Colors.bg_green + result_line + Colors.reset)
        elif result['osm_type'] != 'relation':
            print(Colors.bg_red + result_line + Colors.reset)
        else:
            print(result_line)
    while True:
        sel = input(f"Which result? (1-{len(nmntm_res)} or 0 to cancel): ").strip()
        if sel == "0":
            return None, None
        try:
            si = int(sel)
        except ValueError:
            print("Invalid selection. Enter a number.")
            continue
        if not (1 <= si <= len(nmntm_res)):
            print("Selection out of range. Try again.")
            continue
        chosen = nmntm_res[si - 1]  # convert 1-based choice to 0-based index
        bbox = (
            float(chosen['boundingbox'][2]),  # west (min lon)
            float(chosen['boundingbox'][0]),  # south (min lat)
            float(chosen['boundingbox'][3]),  # east (max lon)
            float(chosen['boundingbox'][1])   # north (max lat)
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