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
from utils.bbox import BBox
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
        # Compute origin lon/lat robustly. Prefer the provided bbox (converted to BBox),
        # fall back to the bounds GeoDataFrame centroid if parsing fails.
        try:
            bbox_obj = BBox(bbox)
            origin_lon = (bbox_obj.west + bbox_obj.east) / 2.0
            origin_lat = (bbox_obj.south + bbox_obj.north) / 2.0
        except Exception:
            try:
                centroid = bounds_gdf.to_crs(4326).geometry.centroid.iloc[0]
                origin_lon = float(centroid.x)
                origin_lat = float(centroid.y)
            except Exception:
                origin_lon, origin_lat = 0.0, 0.0
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
    if current_map.data is {}:
        print("No map data available. Please download a city first.")
        return
    # Generate heightmap and ground texture with defaults
    from processing.heightmap_handler import generate_heightmap_n_texture
    from processing.otc_exporter import export_global_otc, export_paged_otc
    from processing.terrn2_exporter import export_terrn2_entrypoint
    import geopandas as gpd
    from shapely.geometry import box
    import os
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
    roads_tobj_path = None
    try:
        from processing.road_network_formatter import build_roads_from_place  # lazy import
        origin_lon = float(os.environ.get("OSM2TERRN_ORIGIN_LON", "0"))
        origin_lat = float(os.environ.get("OSM2TERRN_ORIGIN_LAT", "0"))
        if place and origin_lon and origin_lat:
            roads_tobj_path = build_roads_from_place(place, origin_lon, origin_lat, tobj_prefix=place)
            if os.path.exists(roads_tobj_path):
                print(f"Procedural roads exported to: {roads_tobj_path}")
            else:
                print(f"Warning: Roads file not created at {roads_tobj_path}")
                roads_tobj_path = None
        else:
            print("Skipping roads export: missing PLACE/ORIGIN env vars.")
    except Exception as e:
        print(f"Skipping roads export due to error: {e}")

    # --- OTC and TERRN2 export ---
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '../output')
        os.makedirs(output_dir, exist_ok=True)
        # Bounds and world size
        bounds_gdf = current_map.data.get('bounds')
        if bounds_gdf is not None:
            minx, miny, maxx, maxy = bounds_gdf.to_crs(4326).total_bounds
            from utils.geometry_utils import compute_world_params, make_square_bounds_centered
            page_size = 1025
            initial_bounds = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs='EPSG:4326')
            world_size, meters_per_pixel = compute_world_params(initial_bounds, page_size=page_size, snap_to_pow2=True)
            bounds = make_square_bounds_centered(initial_bounds, world_size)
            # Export heightmap/groundmap again if needed (already done above)
            # OTC paged
            page_otc = os.path.join(output_dir, f'{place}-page-0-0.otc')
            export_paged_otc(str(page_otc), heightmap_png=os.path.basename(heightmap_path), groundmap_file=os.path.basename(groundmap_path))
            # OTC global
            global_otc = os.path.join(output_dir, f'{place}.otc')
            export_global_otc(
                filepath=str(global_otc),
                page_file_format=f'{place}-page-0-0.otc',
                world_size_x=float(world_size),
                world_size_z=float(world_size),
                world_size_y=250.0,
                pages_x=0,
                pages_z=0,
            )
            # TERRN2 entrypoint
            terrn2 = os.path.join(output_dir, f'{place}.terrn2')
            # Build objects_files list only with files that exist
            objects_files = [f'{place}.tobj']
            if roads_tobj_path and os.path.exists(roads_tobj_path):
                objects_files.append(os.path.basename(roads_tobj_path))
            
            export_terrn2_entrypoint(
                filepath=str(terrn2),
                terrain_name=place,
                geometry_config=os.path.basename(global_otc),
                objects_files=objects_files,
                authors=['osm2terrn', 'OpenStreetMap Contributors', 'YourNickHere'],
            )
            # Minimal .tobj placeholder if not present
            tobj_path = os.path.join(output_dir, f'{place}.tobj')
            if not os.path.exists(tobj_path):
                with open(tobj_path, 'w', encoding='utf-8') as f:
                    f.write('// Placeholder objects; add roads/buildings later\n')
            print('Export complete:')
            print('  -', terrn2)
            print('  -', global_otc)
            print('  -', page_otc)
            print('  -', heightmap_path)
            print('  -', groundmap_path)
            print('  -', tobj_path)
        else:
            print('No bounds data for OTC/TERRN2 export.')
    except Exception as e:
        print(f'Error during OTC/TERRN2 export: {e}')


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
