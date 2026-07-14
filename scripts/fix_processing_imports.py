from pathlib import Path

root = Path('src')
proc = root / 'processing'

mapping = {
    'rail_track_formatter': 'roads',
    'road_elevation': 'roads',
    'road_exporters_blocks': 'roads',
    'road_exporters_utils': 'roads',
    'road_geometry': 'roads',
    'road_merger': 'roads',
    'road_model': 'roads',
    'road_network_export': 'network',
    'road_network_graph_build': 'network',
    'road_network_graph_intersections': 'network',
    'tobj_exporter': 'network',
    'elevation_service': 'terrain',
    'heightmap_handler': 'terrain',
    'terrain_colormap_colors': 'terrain',
    'terrain_colormap_ops': 'terrain',
    'terrn2_entrypoint': 'terrain',
    'terrn2_water': 'terrain',
    'texture_splatting': 'terrain',
    'otc_config': 'otc',
    'otc_global': 'otc',
    'otc_paged': 'otc',
    'otc_utils': 'otc',
}

for path in root.rglob('*.py'):
    if 'site-packages' in str(path):
        continue
    text = path.read_text(encoding='utf-8')
    new_text = text
    for mod, pkg in mapping.items():
        old = f'from processing.{mod} import '
        new = f'from processing.{pkg}.{mod} import '
        new_text = new_text.replace(old, new)
        old2 = f'import processing.{mod}'
        new2 = f'import processing.{pkg}.{mod}'
        new_text = new_text.replace(old2, new2)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')

# Remove wrapper files in processing root, except __init__.py
for fname in mapping.keys():
    wrapper = proc / f'{fname}.py'
    if wrapper.exists():
        wrapper.unlink()

print('Imports updated and old wrappers removed.')
