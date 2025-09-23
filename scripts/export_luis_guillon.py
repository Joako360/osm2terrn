import sys
from pathlib import Path
import os

# Ensure src is importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from processing.heightmap_handler import generate_heightmap_n_texture
from processing.otc_exporter import export_global_otc, export_paged_otc
from processing.terrn2_exporter import export_terrn2_entrypoint
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from utils.geometry_utils import compute_world_params, make_square_bounds_centered

OUTPUT = ROOT / 'output'
OUTPUT.mkdir(exist_ok=True)

terrain_name = 'LuisGuillon'

# 1) Geocode bounds
place = 'Luis Guillón, Esteban Echeverría, Buenos Aires, Argentina'
area = ox.geocode_to_gdf(place)
minx, miny, maxx, maxy = area.to_crs(4326).total_bounds
initial_bounds = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs='EPSG:4326')

page_size = 1025  # 2^n + 1 recommended by Ogre terrain
world_size, meters_per_pixel = compute_world_params(initial_bounds, page_size=page_size, snap_to_pow2=True)
bounds = make_square_bounds_centered(initial_bounds, world_size)

# 2) Generate heightmap + groundmap (size derived from page_size)
heightmap_png = OUTPUT / f'{terrain_name}-heightmap.png'
groundmap_png = OUTPUT / f'{terrain_name}-groundmap.png'
generate_heightmap_n_texture(bounds, heightmap_path=str(heightmap_png), groundmap_path=str(groundmap_png), output_size=(page_size, page_size), smoothing_sigma=0.8)

# 3) Export paged .otc (page-0-0)
page_otc = OUTPUT / f'{terrain_name}-page-0-0.otc'
export_paged_otc(str(page_otc), heightmap_png=str(heightmap_png.name), groundmap_png=str(groundmap_png.name))

# 4) Export global .otc
global_otc = OUTPUT / f'{terrain_name}.otc'
export_global_otc(
    filepath=str(global_otc),
    page_file_format=f'{terrain_name}-page-0-0.otc',
    world_size_x=float(world_size),
    world_size_z=float(world_size),
    world_size_y=250.0,
    pages_x=0,
    pages_z=0,
)

# 5) Export .terrn2 entry
terrn2 = OUTPUT / f'{terrain_name}.terrn2'
export_terrn2_entrypoint(
    filepath=str(terrn2),
    terrain_name=terrain_name,
    geometry_config=global_otc.name,
    objects_files=[f'{terrain_name}.tobj'],
    authors=['osm2terrn'],
)

# 6) Create minimal tobj placeholder
tobj_path = OUTPUT / f'{terrain_name}.tobj'
with open(tobj_path, 'w', encoding='utf-8') as f:
    f.write('// Placeholder objects; add roads/buildings later\n')

print('Export complete:')
print('  -', terrn2)
print('  -', global_otc)
print('  -', page_otc)
print('  -', heightmap_png)
print('  -', groundmap_png)
print('  -', tobj_path)
