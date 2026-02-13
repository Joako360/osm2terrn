import os
import uuid
from typing import Any, List, Dict, Optional
from utils.logger import get_logger, log_info, log_error
from utils.constants import (
    TERRN2_DEFAULT_WATER_ENABLED,
    TERRN2_DEFAULT_WATER_LINE,
    TERRN2_DEFAULT_WATER_BOTTOM_LINE,
    TERRN2_DEFAULT_AMBIENT_COLOR,
    TERRN2_DEFAULT_START_POSITION,
    TERRN2_DEFAULT_START_ROTATION,
    TERRN2_DEFAULT_SANDSTORM_CUBEMAP,
    TERRN2_DEFAULT_GRAVITY,
    TERRN2_DEFAULT_CATEGORY_ID,
    TERRN2_DEFAULT_VERSION,
)

logger = get_logger("terrn2_exporter")


def _generate_guid() -> str:
    """
    Generates a random UUID v4 as a GUID string.

    Returns:
        str: A GUID string in the format 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'.
    """
    return str(uuid.uuid4())


def export_terrn2_entrypoint(
    filepath: str,
    terrain_name: str,
    geometry_config: str,
    objects_files: List[str],
    authors: Optional[Any] = None,
    water_config: Optional[Dict[str, float]] = None,
    ambient_color: Optional[str] = None,
    start_position: Optional[str] = None,
    start_rotation: Optional[float] = None,
    sandstorm_cubemap: Optional[str] = None,
    gravity: Optional[float] = None,
    category_id: Optional[int] = None,
    guid: Optional[str] = None,
    caelum_config: Optional[str] = None,
    traction_map: Optional[str] = None,
    scripts: Optional[List[str]] = None,
    asset_packs: Optional[List[str]] = None,
    ai_presets: Optional[List[str]] = None,
    extra_sections: Optional[Dict[str, Dict[str, str]]] = None
) -> None:
    """
    Generates a comprehensive .terrn2 entry point file for Rigs of Rods.

    This function creates a complete Terrn2 terrain configuration file with support
    for all standard sections and fields, including water settings, ambient lighting,
    starting position, and optional features like scripts and asset packs.

    If no GUID is provided, one will be automatically generated.

    Args:
        filepath (str): Path to the .terrn2 file to create.
        terrain_name (str): Name of the terrain (displayed in terrain selector).
        geometry_config (str): Name of the geometry config file (.otc).
        objects_files (list): List of .tobj files to reference.
        authors (dict, optional): Dictionary of author roles: {role: name}.
            Example: {'terrain': 'Author Name', 'objects': 'Other Author'}
        water_config (dict, optional): Water settings with keys:
            - 'enabled': bool (default: True)
            - 'water_line': float in meters (default: 0.0)
            - 'water_bottom_line': float in meters (default: -150.0)
        ambient_color (str, optional): RGB ambient light as "R, G, B" with values 0-1.
        start_position (str, optional): Spawn position as "X, Y, Z" in local coordinates.
        start_rotation (float, optional): Spawn rotation in degrees (0-360).
        sandstorm_cubemap (str, optional): Cubemap for sandstorm sky type.
        gravity (float, optional): Terrain gravity in m/s² (Earth: -9.81).
        category_id (int, optional): Category ID (129 for addon terrains, 5000 for official).
        guid (str, optional): GUID string for terrain identification.
            If not provided, one will be automatically generated.
        caelum_config (str, optional): Caelum sky/weather config file name.
        traction_map (str, optional): Traction/landuse config file name.
        scripts (list, optional): List of AngelScript files (.as) for terrain logic.
        asset_packs (list, optional): List of asset pack files (.assetpack).
        ai_presets (list, optional): List of AI waypoint files (.json).
        extra_sections (dict, optional): Additional INI sections as {section: {key: value}}.

    Raises:
        Exception: If file writing fails.

    Example:
        >>> export_terrn2_entrypoint(
        ...     filepath="MyTerrain.terrn2",
        ...     terrain_name="My Custom Map",
        ...     geometry_config="MyTerrain.otc",
        ...     objects_files=["MyTerrain.tobj"],
        ...     authors={"terrain": "John Doe", "objects": "Jane Smith"},
        ...     water_config={"enabled": True, "water_line": 50.0},
        ...     start_position="256.0, 10.0, 256.0"
        ...     # GUID will be auto-generated if not provided
        ... )
    """
    try:
        # Prepare water settings
        water_enabled = TERRN2_DEFAULT_WATER_ENABLED
        water_line = TERRN2_DEFAULT_WATER_LINE
        water_bottom_line = TERRN2_DEFAULT_WATER_BOTTOM_LINE

        if water_config:
            water_enabled = 1 if water_config.get("enabled", True) else 0
            water_line = water_config.get("water_line", TERRN2_DEFAULT_WATER_LINE)
            water_bottom_line = water_config.get("water_bottom_line", TERRN2_DEFAULT_WATER_BOTTOM_LINE)

        # Use provided values or defaults
        ambient_color = ambient_color or TERRN2_DEFAULT_AMBIENT_COLOR
        start_position = start_position or TERRN2_DEFAULT_START_POSITION
        start_rotation = start_rotation if start_rotation is not None else TERRN2_DEFAULT_START_ROTATION
        sandstorm_cubemap = sandstorm_cubemap or TERRN2_DEFAULT_SANDSTORM_CUBEMAP
        gravity = gravity if gravity is not None else TERRN2_DEFAULT_GRAVITY
        category_id = category_id if category_id is not None else TERRN2_DEFAULT_CATEGORY_ID

        # Generate GUID if not provided
        if not guid:
            guid = _generate_guid()
            log_info(logger, f"🔑 Generated GUID: {guid}")

        with open(filepath, 'w', encoding='utf-8') as f:
            # Write [General] section
            f.write("[General]\n")
            f.write(f"Name = {terrain_name}\n")
            f.write(f"GeometryConfig = {geometry_config}\n")
            f.write(f"Water = {water_enabled}\n")
            f.write(f"WaterLine = {water_line:.6f}\n")
            f.write(f"WaterBottomLine = {water_bottom_line:.6f}\n")
            f.write(f"AmbientColor = {ambient_color}\n")
            f.write(f"StartPosition = {start_position}\n")
            f.write(f"StartRotation = {start_rotation:.6f}\n")
            f.write(f"Gravity = {gravity:.6f}\n")
            f.write(f"CategoryID = {category_id}\n")
            f.write(f"Version = {TERRN2_DEFAULT_VERSION}\n")
            f.write(f"GUID = {guid}\n")
            f.write(f"SandStormCubeMap = {sandstorm_cubemap}\n")
            
            # Add optional fields if provided
            if caelum_config:
                f.write(f"CaelumConfigFile = {caelum_config}\n")
            if traction_map:
                f.write(f"TractionMap = {traction_map}\n")
            
            f.write("\n")

            # [Authors] section
            if authors:
                f.write("[Authors]\n")
                # If authors is a list of strings, write each as is
                if isinstance(authors, list):
                    for author in authors:
                        f.write(f"{author}\n")
                # If authors is a dict, write as key = value
                elif isinstance(authors, dict):
                    for role, name in authors.items():
                        f.write(f"{role} = {name}\n")
                f.write("\n")

            # [AssetPacks] section (optional)
            if asset_packs:
                f.write("[AssetPacks]\n")
                for asset_pack in asset_packs:
                    f.write(f"{asset_pack}=\n")
                f.write("\n")

            # [Objects] section
            f.write("[Objects]\n")
            for obj_file in objects_files:
                f.write(f"{obj_file}=\n")
            f.write("\n")

            # [Scripts] section (optional)
            if scripts:
                f.write("[Scripts]\n")
                for script in scripts:
                    f.write(f"{script}=\n")
                f.write("\n")

            # [AI Presets] section (optional)
            if ai_presets:
                f.write("[AI Presets]\n")
                for preset in ai_presets:
                    f.write(f"{preset}=\n")
                f.write("\n")

            # Extra custom sections
            if extra_sections:
                for section, values in extra_sections.items():
                    f.write(f"[{section}]\n")
                    for key, value in values.items():
                        f.write(f"{key} = {value}\n")
                    f.write("\n")

        log_info(logger, f"✅ Successfully exported terrn2 entry point to {filepath}")

    except IOError as e:
        log_error(logger, f"❌ I/O error while exporting terrn2: {e}")
        raise
    except Exception as e:
        log_error(logger, f"❌ Failed to export terrn2 entry point: {e}")
        raise
