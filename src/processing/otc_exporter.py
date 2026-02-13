import os
from typing import Any, List, Dict, Optional
from utils.logger import get_logger, log_info, log_error, log_warning

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
    Deprecated: This function writes a non-OGRE '[Terrain]' style file.
    Prefer export_global_otc (OGRE global .otc) and export_paged_otc (paged .otc)
    to comply with Terrn2/OGRE configs.
    """
    try:
        log_warning(logger, "export_otc_config is deprecated. Use export_global_otc/export_paged_otc for OGRE .otc files.")
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
    page_size: int = 1025,
    pages_x: int = 0,
    pages_z: int = 0,
    # Heightmap options: provide when using RAW. PNG does not need these keys.
    # Example: {"format": "raw", "size": 1025, "bpp": 2, "flip_x": False, "flip_y": False}
    heightmap: Optional[Dict[str, Any]] = None,
    layer_blend_map_size: int = 1024,
    min_batch_size: int = 33,
    max_batch_size: int = 65,
    disable_caching: bool = True,
    extra_settings: Optional[Dict[str, str]] = None,
) -> None:
    """
    Export an OGRE-style global .otc config that references paged .otc files.

    Writes:
    - PagesX/PagesZ
    - PageFileFormat
    - WorldSizeX/Z/Y
    - PageSize
    - Flat=0
    - (Optional RAW heightmap keys) Heightmap.0.0.raw.size/bpp/flipX/flipY
    - LayerBlendMapSize
    - disableCaching
    - Batch sizes and sensible rendering defaults

    Parameters:
        heightmap: If provided with format='raw', writes RAW-specific keys.
                   For PNG heightmaps, omit or set format='png' (no RAW keys written).
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # RAW heightmap keys if requested (must come first)
            if heightmap:
                fmt = str(heightmap.get("format", "raw")).lower()
                if fmt == "raw":
                    size = int(heightmap.get("size", page_size))
                    bpp = int(heightmap.get("bpp", 2))
                    flip_x = 1 if bool(heightmap.get("flip_x", False)) else 0
                    f.write(f"Heightmap.0.0.raw.size={size}\n")
                    f.write(f"Heightmap.0.0.raw.bpp={bpp}\n")
                    f.write(f"Heightmap.0.0.flipX={flip_x}\n")
                    f.write("\n")

            # World (XY) size in meters
            f.write(f"WorldSizeX={int(world_size_x)}\n")
            f.write(f"WorldSizeZ={int(world_size_z)}\n")
            f.write(f"WorldSizeY={int(world_size_y)}\n")
            f.write(f"PageSize={int(page_size)}\n")
            f.write(" \n")  # Space before newline like in example
            
            f.write("disableCaching=1\n" if disable_caching else "disableCaching=0\n")
            f.write(" \n")
            
            f.write(f"PageFileFormat={page_file_format}\n")

            f.write("\n")
            
            # Rendering settings
            f.write(f"MaxPixelError=1\n")
            f.write(f"LightmapEnabled=0\n")  # Match example
            f.write(f"SpecularMappingEnabled=1\n")
            f.write(f"NormalMappingEnabled=1\n")
            
            # Apply extra settings if provided
            if extra_settings:
                for k, v in extra_settings.items():
                    f.write(f"{k}={v}\n")
        log_info(logger, f"Exported global .otc to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export global .otc: {e}")


def export_paged_otc(
    filepath: str,
    heightmap_png: str,
    groundmap_file: Optional[str] = None,
    layers: Optional[List[Dict[str, object]]] = None,
) -> None:
    """
    Export a paged .otc file for textures/blending.

    Format:
    - 1st line: heightmap file name (PNG or RAW file name)
    - 2nd line: number of layers (1-6). Layer #0 is the ground layer (no blendmap)
    - 3rd line: header
    - Following: layer rows "worldSize, diffusespecular, normalheight, [blendmap], [blendmapmode], [alpha]"

    Notes:
    - The ground layer covers entire terrain (no blendmap, only 3 fields).
    - Preserves the input order of 'layers' after the ground layer.
    """
    try:
        # Default ground/base layer (covers entire page)
        base_layer = {
            "worldSize": 6,                        # tiling scale
            "diffuse": "terrain_detail.dds",
            "normal": "blank_NRM.dds",
        }

        # Provide simple defaults using stock textures if layers not provided
        if layers is None:
            layers = []
            if groundmap_file:
                gm = os.path.basename(groundmap_file)
                layers = [
                    {"worldSize": 6, "diffuse": "terrain_detail.dds", "normal": "blank_NRM.dds", "blend": gm, "blendmode": "R", "alpha": 0.5},
                    {"worldSize": 6, "diffuse": "terrain_grass.dds",  "normal": "blank_NRM.dds", "blend": gm, "blendmode": "G", "alpha": 0.5},
                ]

        total_layers = 1 + (len(layers) if layers else 0)
        if total_layers < 1 or total_layers > 6:
            log_error(logger, f"Paged .otc layers must be in range 1-6; got {total_layers}.")
            total_layers = max(1, min(total_layers, 6))
            # If over, truncate extra layers
            if layers and (1 + len(layers)) > 6:
                layers = layers[:5]  # keep ground + first 5

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{os.path.basename(heightmap_png)}\n")
            f.write(f"{total_layers}\n")
            f.write("; worldSize, diffusespecular, normalheight, blendmap, blendmapmode, alpha\n")

            # Ground/base layer (no blendmap)
            f.write(f"{int(base_layer['worldSize'])}, {base_layer['diffuse']}, {base_layer['normal']}\n")

            # Additional layers (preserve input order)
            for L in (layers or []):
                world_size = int(L.get("worldSize", 6)) #type: ignore
                diffuse = str(L.get("diffuse", "terrain_detail.dds"))
                normal = str(L.get("normal", "blank_NRM.dds"))
                blend = L.get("blend")
                blendmode = str(L.get("blendmode", "R"))
                alpha = float(L.get("alpha", 0.5)) #type: ignore
                if blend is None:
                    # No blendmap provided -> treat as ground-like layer (rare)
                    f.write(f"{world_size}, {diffuse}, {normal}\n")
                else:
                    f.write(f"{world_size}, {diffuse}, {normal}, {os.path.basename(str(blend))}, {blendmode}, {alpha}\n")

            f.write("\n")  # Ensure final newline

        log_info(logger, f"Exported paged .otc to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export paged .otc: {e}")
