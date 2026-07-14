import sys
import os
from pathlib import Path
import argparse

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
from processing.otc_exporter import export_global_otc, export_paged_otc
from processing.terrn2_exporter import export_terrn2_entrypoint
from osm2terrn.utils.geometry.bounds import compute_world_params, make_square_bounds_centered


DEFAULT_PLACE = 'Luis Guillón, Esteban Echeverría, Buenos Aires, Argentina'


def geocode_bounds(place: str):
	area = ox.geocode_to_gdf(place)
	minx, miny, maxx, maxy = area.to_crs(4326).total_bounds
	return gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs='EPSG:4326')


def run_smoke(place: str = DEFAULT_PLACE):
	print('Geocoding place:', place)
	bounds = geocode_bounds(place)
	print('Bounds:', bounds.total_bounds)
	print('Generating heightmaps (smoke test)...')
	os.makedirs('output', exist_ok=True)
	generate_heightmap_n_texture(bounds, heightmap_path='output/heightmap.png', groundmap_path='output/groundmap.png', output_size=(512, 512), smoothing_sigma=0.8)
	print('Smoke export done:')
	print('  -', Path('output/heightmap.png').resolve())
	print('  -', Path('output/groundmap.png').resolve())


def run_full_export(place: str = DEFAULT_PLACE, terrain_name: str = 'LuisGuillon', page_size: int = 1025):

	print('Geocoding place:', place)
	area = ox.geocode_to_gdf(place)
	minx, miny, maxx, maxy = area.to_crs(4326).total_bounds
	initial_bounds = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs='EPSG:4326')

	print('Computing world parameters...')
	world_size, meters_per_pixel = compute_world_params(initial_bounds, page_size=page_size, snap_to_pow2=True)
	bounds = make_square_bounds_centered(initial_bounds, world_size)

	OUTPUT = ROOT / 'output'
	OUTPUT.mkdir(exist_ok=True)

	# 2) Generate heightmap + groundmap (size derived from page_size)
	heightmap_png = OUTPUT / f'{terrain_name}-heightmap.png'
	groundmap_png = OUTPUT / f'{terrain_name}-groundmap.png'
	print('Generating full-resolution heightmaps...')
	generate_heightmap_n_texture(bounds, heightmap_path=str(heightmap_png), groundmap_path=str(groundmap_png), output_size=(page_size, page_size), smoothing_sigma=0.8)

	# 3) Export paged .otc (page-0-0)
	page_otc = OUTPUT / f'{terrain_name}-page-0-0.otc'
	print('Exporting paged .otc...')
	export_paged_otc(str(page_otc), heightmap_png=str(heightmap_png.name), groundmap_file=str(groundmap_png.name))

	# 4) Export global .otc
	global_otc = OUTPUT / f'{terrain_name}.otc'
	print('Exporting global .otc...')
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
	print('Exporting .terrn2 entry...')
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

	print('Full export complete:')
	print('  -', terrn2)
	print('  -', global_otc)
	print('  -', page_otc)
	print('  -', heightmap_png)
	print('  -', groundmap_png)
	print('  -', tobj_path)


def main():
	parser = argparse.ArgumentParser(description='Smoke/full exporter for Luis Guillón')
	parser.add_argument('--mode', choices=['smoke', 'export', 'all'], default='smoke', help='Modo a ejecutar')
	parser.add_argument('--place', default=DEFAULT_PLACE, help='Texto de geocoding para la ubicación')
	parser.add_argument('--terrain-name', default='LuisGuillon', help='Nombre base para archivos de salida')
	parser.add_argument('--page-size', type=int, default=1025, help='Tamaño de página para export completo')

	args = parser.parse_args()

	if args.mode in ('smoke', 'all'):
		run_smoke(args.place)
	if args.mode in ('export', 'all'):
		run_full_export(place=args.place, terrain_name=args.terrain_name, page_size=args.page_size)


if __name__ == '__main__':
	main()
