import os
from typing import List, Dict, Optional
from utils.logger import get_logger, log_info, log_error

logger = get_logger("otc_exporter")


def export_otc_config(
    filepath: str,
    terrain_name: str,
    heightmap_file: str,
    groundmap_file: str,
    bounds: Optional[List[float]] = None,
    extra_settings: Optional[Dict[str, str]] = None
) -> None:
    """
    Generates a .otc geometry config file for Rigs of Rods terrain.

    Example output:
    [Terrain]
    Name = MyTerrain
    Heightmap = heightmap.png
    Groundmap = groundmap.png
    Bounds = -500.00 -500.00 500.00 500.00
    CellSize = 2.0
    TextureRepeat = 1.0

    Args:
        filepath (str): Path to the .otc file to create.
        terrain_name (str): Name of the terrain.
        heightmap_file (str): Path to the heightmap image.
        groundmap_file (str): Path to the ground texture image.
        bounds (list, optional): [min_x, min_y, max_x, max_y] in meters.
        extra_settings (dict, optional): Additional config key-value pairs.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"[Terrain]\n")
            f.write(f"Name = {terrain_name}\n")
            f.write(f"Heightmap = {heightmap_file}\n")
            f.write(f"Groundmap = {groundmap_file}\n")
            if bounds and len(bounds) == 4:
                f.write(f"Bounds = {bounds[0]:.2f} {bounds[1]:.2f} {bounds[2]:.2f} {bounds[3]:.2f}\n")
            # Example of recommended fields by the instructions
            f.write("CellSize = 2.0\n")
            f.write("TextureRepeat = 1.0\n")
            if extra_settings:
                for key, value in extra_settings.items():
                    f.write(f"{key} = {value}\n")
            f.write("\n")
        log_info(logger, f"Successfully exported .otc config to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export .otc config: {e}")


def export_global_otc(
    filepath: str,
    page_file_format: str,
    world_size_x: float,
    world_size_z: float,
    world_size_y: float = 300.0,
    pages_x: int = 0,
    pages_z: int = 0,
    layer_blend_map_size: int = 2048,
    min_batch_size: int = 17,
    max_batch_size: int = 65,
    disable_caching: int = 1,
    extra_settings: Optional[Dict[str, str]] = None,
) -> None:
    """
    Export an OGRE-style global .otc config that references paged .otc files.

    Follows the conventions in .github/instructions/exporters.instructions.md
    and examples in examples/template_04_png/.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# the amount of pages in this terrain\n")
            f.write("# 0, 0 means that you only have one page\n")
            f.write(f"PagesX={pages_x}\n")
            f.write(f"PagesZ={pages_z}\n\n")

            f.write(f"PageFileFormat={page_file_format}\n\n")

            f.write("# the factor with what the heightmap values get multiplied with\n")
            f.write(f"WorldSizeY={int(world_size_y)}\n\n")

            f.write("# The world size of the terrain\n")
            f.write(f"WorldSizeX={int(world_size_x)}\n")
            f.write(f"WorldSizeZ={int(world_size_z)}\n\n")

            f.write(f"LayerBlendMapSize={int(layer_blend_map_size)}\n\n")

            if disable_caching:
                f.write("disableCaching=1\n\n")

            f.write(f"minBatchSize={int(min_batch_size)}\n")
            f.write(f"maxBatchSize={int(max_batch_size)}\n\n")

            # Sensible defaults; can be overridden with extra_settings
            defaults = {
                "LightmapEnabled": "1",
                "NormalMappingEnabled": "1",
                "SpecularMappingEnabled": "1",
                "ParallaxMappingEnabled": "0",
                "GlobalColourMapEnabled": "0",
                "ReceiveDynamicShadowsDepth": "0",
                "CompositeMapSize": "1024",
                "CompositeMapDistance": "5000",
                "SkirtSize": "30",
                "LightMapSize": "1024",
                "CastsDynamicShadows": "0",
                "MaxPixelError": "1",
                "DebugBlendMaps": "0",
            }
            if extra_settings:
                defaults.update({k: str(v) for k, v in extra_settings.items()})
            for k, v in defaults.items():
                f.write(f"{k}={v}\n")
            f.write("\n")
        log_info(logger, f"Exported global .otc to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export global .otc: {e}")


def export_paged_otc(
    filepath: str,
    heightmap_png: str,
    groundmap_png: str,
    layers: Optional[list[dict]] = None,
) -> None:
    """
    Export a paged .otc file for textures/blending.

    Format:
    - 1st line: heightmap PNG filename
    - 2nd line: number of layers
    - 3rd line: header
    - Following: layer rows "worldSize, diffusespecular, normalheight, blendmap, blendmapmode, alpha"
    """
    try:
        # Provide two simple layers using stock textures and the generated groundmap as blendmap
        if layers is None:
            layers = [
                {"worldSize": 6, "diffuse": "terrain_detail.dds", "normal": "blank_NRM.dds", "blend": groundmap_png, "blendmode": "R", "alpha": 0.5},
                {"worldSize": 6, "diffuse": "terrain_grass.dds",  "normal": "blank_NRM.dds", "blend": groundmap_png, "blendmode": "G", "alpha": 0.5},
            ]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{os.path.basename(heightmap_png)}\n")
            f.write(f"{len(layers)}\n")
            f.write("; worldSize, diffusespecular, normalheight, blendmap, blendmapmode, alpha\n")
            for L in layers:
                f.write(f"{int(L['worldSize'])}, {L['diffuse']}, {L['normal']}, {os.path.basename(L['blend'])}, {L['blendmode']}, {float(L['alpha'])}\n")
        log_info(logger, f"Exported paged .otc to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export paged .otc: {e}")
