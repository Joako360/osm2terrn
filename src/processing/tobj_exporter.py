import os
from typing import Dict, List
from processing.road_network_formatter import Road
from utils.constants import Colors
from utils.logger import get_logger, log_info, log_error, log_warning

logger = get_logger("tobj_exporter")

class TobjExporter:
    """
    Handles the export of various processed geographic data into the .tobj file format
    used by Rigs of Rods.
    """

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the TobjExporter with the specified output directory.

        Args:
            output_dir (str): Directory where .tobj files will be saved.
        """
        self.output_dir = output_dir
        log_info(logger, f"TobjExporter initialized with output directory: {self.output_dir}")

    def export_to_tobj(self, data: Dict, filename: str = "output.tobj") -> None:
        """
        Export processed data (roads, bounds, etc.) to a .tobj file.

        Args:
            data (Dict): Dictionary containing processed data. Expected keys: 'roads', 'bounds'.
            filename (str): Name of the .tobj file to create.
        """
        from processing.road_network_formatter import to_procedural_roads_block  # Import here for modularity
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w') as f:
                f.write("TOBJ\n")
                f.write("version 1.0\n")
                f.write("\n")

                # Export bounds (example, adjust as needed for tobj format)
                if 'bounds' in data and hasattr(data['bounds'], 'empty') and not data['bounds'].empty:
                    bounds = data['bounds'].total_bounds
                    f.write(f"bounds {bounds[0]:.6f} {bounds[1]:.6f} {bounds[2]:.6f} {bounds[3]:.6f}\n")
                    log_info(logger, "Exported bounds to tobj.")
                else:
                    log_warning(logger, "No bounds data found for tobj export.")

                # Export roads using the correct formatter
                if 'roads' in data and isinstance(data['roads'], list):
                    f.write("\n# Roads\n")
                    roads_block = to_procedural_roads_block(data['roads'])
                    f.write(roads_block + "\n")
                    log_info(logger, f"Exported {len(data['roads'])} roads to tobj.")
                else:
                    log_warning(logger, "No roads data found for tobj export.")
            log_info(logger, f"Successfully exported data to {filepath}")
        except Exception as e:
            log_error(logger, f"Failed to export data to tobj: {e}")

    def export_roads(self, roads: List[Road], filepath: str) -> None:
        """
        Export a list of Road objects to a .tobj file.

        Args:
            roads (List[Road]): List of Road objects to export.
            filepath (str): Path to the .tobj file to create.
        """
        try:
            with open(filepath, 'w') as f:
                f.write("TOBJ\n")
                f.write("version 1.0\n")
                f.write("\n# Roads\n")
                for road in roads:
                    if hasattr(road, "to_tobj_string"):
                        f.write(f"road {road.to_tobj_string()}\n")
                    else:
                        log_error(logger, "Road object missing 'to_tobj_string' method.")
            log_info(logger, f"Successfully exported {len(roads)} roads to {filepath}")
        except Exception as e:
            log_error(logger, f"Failed to export roads to tobj: {e}")
    
    def export_buildings(self, buildings: List, filepath: str) -> None:
        """
        Export building data to a .tobj file.

        Args:
            buildings (List): List of building geometries or objects to export.
            filepath (str): Path to the .tobj file to create.
        """
        try:
            with open(filepath, 'w') as f:
                f.write("TOBJ\n")
                f.write("version 1.0\n")
                f.write("\n# Buildings\n")
                for building in buildings:
                    if hasattr(building, "to_tobj_string"):
                        f.write(f"building {building.to_tobj_string()}\n")
                    else:
                        log_error(logger, "Building object missing 'to_tobj_string' method.")
            log_info(logger, f"Successfully exported {len(buildings)} buildings to {filepath}")
        except Exception as e:
            log_error(logger, f"Failed to export buildings to tobj: {e}")