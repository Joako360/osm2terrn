"""
Rail Track Formatter for OSM2terrn
Generates rail segments and train stations for terrain export (.tobj).
Follows conventions in exporters.instructions.md
"""

from typing import List, Tuple, Dict, Optional
import math
from utils.logger import get_logger, log_info, log_error

logger = get_logger("rail_track_formatter")

class RailSegment:
    """
    Represents a single rail track segment for terrain export.

    Attributes:
        x (float): Local X coordinate in meters.
        y (float): Local Y coordinate in meters.
        z (float): Local Z coordinate in meters.
        yaw (float): Yaw rotation in degrees.
        pitch (float): Pitch rotation in degrees.
        roll (float): Roll rotation in degrees.
        mesh (str): Mesh file name for the rail segment.
    """

    def __init__(self, x: float, y: float, z: float, yaw: float, pitch: float, roll: float, mesh: str):
        """
        Initialize a RailSegment instance.

        Args:
            x (float): Local X coordinate in meters.
            y (float): Local Y coordinate in meters.
            z (float): Local Z coordinate in meters.
            yaw (float): Yaw rotation in degrees.
            pitch (float): Pitch rotation in degrees.
            roll (float): Roll rotation in degrees.
            mesh (str): Mesh file name for the rail segment.
        """

        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll
        self.mesh = mesh

    def to_tobj_line(self) -> str:
        """
        Format the rail segment as a line for .tobj export.

        Returns:
            str: Formatted .tobj line for this rail segment.
        """
        return f"{self.x:.3f}, {self.y:.3f}, {self.z:.3f}, {self.yaw:.6f}, {self.pitch:.6f}, {self.roll:.6f}, rail {self.mesh}"

class TrainStation:
    """
    Represents a train station spawner for terrain export.

    Attributes:
        x (float): Local X coordinate in meters.
        y (float): Local Y coordinate in meters.
        z (float): Local Z coordinate in meters.
        yaw (float): Yaw rotation in degrees.
        pitch (float): Pitch rotation in degrees.
        roll (float): Roll rotation in degrees.
        mesh (str): Mesh file name for the train station spawner.
    """
    
    def __init__(self, x: float, y: float, z: float, yaw: float, pitch: float, roll: float, mesh: str):
        """
        Initialize a TrainStation instance.

        Args:
            x (float): Local X coordinate in meters.
            y (float): Local Y coordinate in meters.
            z (float): Local Z coordinate in meters.
            yaw (float): Yaw rotation in degrees.
            pitch (float): Pitch rotation in degrees.
            roll (float): Roll rotation in degrees.
            mesh (str): Mesh file name for the train station spawner.
        """
        
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll
        self.mesh = mesh

    def to_tobj_line(self) -> str:
        """
        Format the train station as a line for .tobj export.

        Returns:
            str: Formatted .tobj line for this train station spawner.
        """
        
        return f"{self.x:.3f}, {self.y:.3f}, {self.z:.3f}, {self.yaw:.6f}, {self.pitch:.6f}, {self.roll:.6f}, trainspawner {self.mesh}"

def export_rails_and_stations(
    rails: List[RailSegment],
    stations: List[TrainStation],
    filepath: str,
    collision_tris: Optional[int] = None,
    extra_comments: Optional[List[str]] = None
) -> None:
    """
    Export rail segments and train stations to a .tobj file for Terrn2.

    Args:
        rails (List[RailSegment]): List of rail segments to export.
        stations (List[TrainStation]): List of train station spawners to export.
        filepath (str): Output .tobj file path.
        collision_tris (Optional[int]): Optional collision-tris header value.
        extra_comments (Optional[List[str]]): Optional list of comments to add at the top of the file.

    Returns:
        None
    """
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if collision_tris:
                f.write(f"collision-tris {collision_tris}\n")
            if extra_comments:
                for comment in extra_comments:
                    f.write(f"// {comment}\n")
            for rail in rails:
                f.write(rail.to_tobj_line() + "\n")
            for station in stations:
                f.write(station.to_tobj_line() + "\n")
            f.write("\n")
        log_info(logger, f"Exported {len(rails)} rails and {len(stations)} stations to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export rails/stations: {e}")
