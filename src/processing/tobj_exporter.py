import os
from typing import Dict, List, Optional
from dataclasses import dataclass

from processing.road_model import Road
from processing.road_exporters import export_procedural_roads_block
from utils.logger import get_logger, log_info, log_error, log_warning

logger = get_logger("tobj_exporter")


@dataclass
class TObject:
    """Represents an object instance in a .tobj file."""
    x: float
    y: float
    z: float
    yaw: float
    pitch: float
    roll: float
    obj_type: str
    obj_file: str
    comment: Optional[str] = None

    def to_tobj_line(self) -> str:
        """Convert the object to a .tobj line format."""
        # Coordinates could be formatted with {:.6f} as per repo-wide conventions, but
        # we keep rotations and precision consistent with examples here.
        line = f"{self.x:.6f}, {self.y:.6f}, {self.z:.6f}, {self.yaw:.6f}, {self.pitch:.6f}, {self.roll:.6f}, {self.obj_type} {self.obj_file}"
        if self.comment:
            line = f"// {self.comment}\n{line}"
        return line


class TobjExporter:
    """
    Handles the export of various processed geographic data into the .tobj file format
    used by Rigs of Rods Terrn2.
    """

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the TobjExporter with the specified output directory.

        Args:
            output_dir (str): Directory where .tobj files will be saved.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        log_info(logger, f"📦 TobjExporter initialized with output directory: {self.output_dir}")

    def export_to_tobj(
        self, 
        roads: Optional[List[Road]] = None,
        objects: Optional[List[TObject]] = None,
        collision_tris: Optional[int] = None,
        filename: str = "output.tobj",
        include_procedural_roads: bool = True
    ) -> None:
        """
        Export processed data (roads, objects, etc.) to a .tobj file.

        Terrn2 supports and prefers procedural roads for road geometry. When
        include_procedural_roads is True and roads are provided, a procedural
        roads section will be emitted.

        Args:
            roads (Optional[List[Road]]): List of Road objects for procedural roads.
            objects (Optional[List[TobjObject]]): List of object instances to place.
            collision_tris (Optional[int]): Number of collision triangles (optional header).
            filename (str): Name of the .tobj file to create.
            include_procedural_roads (bool): Whether to include procedural roads block.
        """
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write collision-tris header if provided
                if collision_tris is not None:
                    f.write(f"collision-tris {collision_tris}\n\n")
                    log_info(logger, f"Added collision-tris header: {collision_tris}")

                # Write object instances section
                if objects and len(objects) > 0:
                    f.write("// Object instances\n")
                    for obj in objects:
                        f.write(obj.to_tobj_line() + "\n")
                    f.write("\n")
                    log_info(logger, f"✅ Exported {len(objects)} object instances")

                # Write procedural roads section using centralized function
                if include_procedural_roads and roads and len(roads) > 0:
                    procedural_block = export_procedural_roads_block(roads, per_segment=False)
                    f.write(procedural_block)
                    f.write("\n\n")
                    log_info(logger, f"🛣️  Exported {len(roads)} roads via procedural roads section")
                elif include_procedural_roads:
                    log_warning(logger, "No roads data provided for procedural roads section")

                # Ensure file ends with newline
                f.write("\n")

            log_info(logger, f"✅ Successfully exported data to {filepath}")
        except Exception as e:
            log_error(logger, f"❌ Failed to export data to tobj: {e}")
            raise

    def export_roads_only(self, roads: List[Road], filepath: str) -> None:
        """
        Export only roads to a .tobj file (without object instances).
        Uses the centralized procedural road export function.

        Args:
            roads (List[Road]): List of Road objects to export.
            filepath (str): Full path to the .tobj file to create.
        """
        try:
            procedural_block = export_procedural_roads_block(roads, per_segment=False)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(procedural_block)
                f.write("\n\n")
            log_info(logger, f"✅ Successfully exported {len(roads)} roads (procedural) to {filepath}")
        except Exception as e:
            log_error(logger, f"❌ Failed to export roads to tobj: {e}")
            raise

    def export_objects_only(self, objects: List[TObject], filepath: str, collision_tris: Optional[int] = None) -> None:
        """
        Export only object instances to a .tobj file (without procedural roads).

        Args:
            objects (List[TobjObject]): List of TobjObject instances to export.
            filepath (str): Full path to the .tobj file to create.
            collision_tris (Optional[int]): Number of collision triangles (optional header).
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if collision_tris is not None:
                    f.write(f"collision-tris {collision_tris}\n\n")
                
                for obj in objects:
                    f.write(obj.to_tobj_line() + "\n")
                f.write("\n")
            log_info(logger, f"✅ Successfully exported {len(objects)} objects to {filepath}")
        except Exception as e:
            log_error(logger, f"❌ Failed to export objects to tobj: {e}")
            raise

    def export_grouped_objects(
        self,
        object_groups: Dict[str, List[TObject]],
        filepath: str,
        collision_tris: Optional[int] = None
    ) -> None:
        """
        Export object instances grouped by category with section comments.

        Args:
            object_groups (Dict[str, List[TobjObject]]): Dictionary mapping group names to lists of objects.
            filepath (str): Full path to the .tobj file to create.
            collision_tris (Optional[int]): Number of collision triangles (optional header).
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if collision_tris is not None:
                    f.write(f"collision-tris {collision_tris}\n\n")

                for group_name, objects in object_groups.items():
                    if objects:
                        f.write(f"// {group_name}\n")
                        for obj in objects:
                            f.write(obj.to_tobj_line() + "\n")
                        f.write("\n")
                        log_info(logger, f"Exported {len(objects)} objects in group '{group_name}'")

                f.write("\n")
            log_info(logger, f"✅ Successfully exported grouped objects to {filepath}")
        except Exception as e:
            log_error(logger, f"❌ Failed to export grouped objects to tobj: {e}")
            raise