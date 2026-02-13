import os
import sys
from pathlib import Path
# Make 'src' importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
	sys.path.insert(0, str(SRC))
from dotenv import load_dotenv
load_dotenv()
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from processing.heightmap_handler import generate_heightmap_n_texture

place = 'Luis Guillón, Esteban Echeverría, Buenos Aires, Argentina'
print('Geocoding place:', place)
area = ox.geocode_to_gdf(place)
minx, miny, maxx, maxy = area.to_crs(4326).total_bounds
bounds = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs='EPSG:4326')
print('Bounds:', bounds.total_bounds)
print('Generating heightmaps...')
os.makedirs('output', exist_ok=True)
generate_heightmap_n_texture(bounds, heightmap_path='output/heightmap.png', groundmap_path='output/groundmap.png', output_size=(512,512), smoothing_sigma=0.8)
print('Done.')
