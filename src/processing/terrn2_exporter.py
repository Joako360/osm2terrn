import os
from typing import List, Dict, Optional
from utils.logger import get_logger, log_info, log_error

logger = get_logger("terrn2_exporter")

def export_terrn2_entrypoint(
    filepath: str,
    terrain_name: str,
    geometry_config: str,
    objects_files: List[str],
    authors: Optional[List[str]] = None,
    extra_sections: Optional[Dict[str, Dict[str, str]]] = None
) -> None:
    """
    Generates a .terrn2 entry point file for Rigs of Rods.

    Args:
        filepath (str): Path to the .terrn2 file to create.
        terrain_name (str): Name of the terrain.
        geometry_config (str): Name of the geometry config file (.otc).
        objects_files (list): List of .tobj files to reference.
        authors (list, optional): List of author names.
        extra_sections (dict, optional): Additional INI sections as {section: {key: value}}.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("[General]\n")
            f.write(f"Name = {terrain_name}\n")
            f.write(f"GeometryConfig = {geometry_config}\n")
            f.write("Version = 2\n")
            f.write("\n")

            if authors:
                f.write("[Authors]\n")
                for author in authors:
                    f.write(f"{author}\n")
                f.write("\n")

            f.write("[Objects]\n")
            for obj_file in objects_files:
                f.write(f"{obj_file}=\n")
            f.write("\n")

            if extra_sections:
                for section, values in extra_sections.items():
                    f.write(f"[{section}]\n")
                    for key, value in values.items():
                        f.write(f"{key} = {value}\n")
                    f.write("\n")
            # Final newline
            f.write("\n")
        log_info(logger, f"Successfully exported terrn2 entry point to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export terrn2 entry point: {e}")
