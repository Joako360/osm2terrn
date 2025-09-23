# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 20:27:25 2021

@author: Joako360
"""
from processing.heightmap_handler import fetch_elevation_from_api as heightmapper
import geopandas as gpd
import os
import sys
from data.osm_data_handler import download_data_from_bbox
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Add the parent directory to the system path

load_dotenv()

class MapData:
    """
    Stores map data, bounds, and heightmap for the current session.
    """
    def __init__(self):
        self.data = {}
        self.elevation_data = {}


current_map = MapData()


def dlcity() -> None:
    clear()
    print("Download map data.")
    from data.osm_data_handler import download_menu
    place, bbox = download_menu()
    if not place or not bbox:
        print("No place or bounding box selected. Returning to main menu.")
        return
    data = download_data_from_bbox(bbox)
    bounds_gdf = data.get('bounds')
    if bounds_gdf is not None:
        # Use bbox center to avoid centroid on geographic CRS warning
        west, south, east, north = bbox
        origin_lon = (west + east) / 2.0
        origin_lat = (south + north) / 2.0
        os.environ['OSM2TERRN_PLACE_NAME'] = place
        os.environ['OSM2TERRN_ORIGIN_LON'] = str(origin_lon)
        os.environ['OSM2TERRN_ORIGIN_LAT'] = str(origin_lat)
        current_map.data = data
        # Try to fetch elevation
        try:
            elevation, maxh, minh = heightmapper(bounds_gdf)
            current_map.elevation_data = {'elevation': elevation, 'maxh': maxh, 'minh': minh}
        except Exception:
            current_map.elevation_data = {}
    else:
        print("Error: No bounds data available from bounding box.")
        current_map.data = {}
        current_map.elevation_data = {}
    return


def load() -> None:
    print('loading...')
    pass


def export() -> None:
    if "bounds" not in current_map.data or "roads" not in current_map.data:
        print("No map data available. Please download a city first.")
        return
    # Generate heightmap and ground texture with defaults
    from processing.heightmap_handler import generate_heightmap_n_texture
    place = os.environ.get("OSM2TERRN_PLACE_NAME") or "terrain"
    heightmap_path = f"output/{place}_heightmap.png"
    groundmap_path = f"output/{place}_groundmap.png"
    generate_heightmap_n_texture(
        current_map.data['bounds'],
        heightmap_path=heightmap_path,
        groundmap_path=groundmap_path,
        elevation_data=current_map.elevation_data
    )
    # Procedural roads export (optional, depends on available API)
    try:
        from processing.road_network_formatter import build_roads_from_place  # lazy import
        place = os.environ.get("OSM2TERRN_PLACE_NAME") or "terrain"
        origin_lon = float(os.environ.get("OSM2TERRN_ORIGIN_LON", "0"))
        origin_lat = float(os.environ.get("OSM2TERRN_ORIGIN_LAT", "0"))
        if place and origin_lon and origin_lat:
            tobj_path = build_roads_from_place(place, origin_lon, origin_lat, tobj_prefix=place)
            print(f"Procedural roads exported to: {tobj_path}")
        else:
            print("Skipping roads export: missing PLACE/ORIGIN env vars.")
    except Exception as e:
        print(f"Skipping roads export due to error: {e}")


def exit() -> None:

    print('exit...')
    raise SystemExit(0)


def clear() -> None:
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

# menu class with labels and function calls for each option


class Menu:
    label = {}
    func = {}

    def __init__(self, title, label, func):
        self.title = title
        self.label = label
        self.func = func

    def show(self):
        # clear()
        print('\n' + '-'*len(self.title))
        print(self.title)
        print('-'*len(self.title))
        for key, value in self.label.items():
            print(f'{key}. {value}')

    def run(self):
        while True:
            self.show()
            choice = input('\nChoose an option: ')
            if choice in self.func:
                self.func[choice]()
            else:
                print('\n' + '*'*len(self.title))
                print('*'*len(self.title))
                print(f'{choice} is not a valid option')
                print('*'*len(self.title))
                input('\npress enter to continue...')


# main menu object
mainmenu = Menu('Main Menu', {
    '1': 'Download City',
    '2': 'Load/Import',
    '3': 'Export',
    '4': 'Exit'
}, {
    '1': dlcity,
    '2': load,
    '3': export,
    '4': exit
})
mainmenu.run()
