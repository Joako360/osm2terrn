from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

Point3D = Tuple[float, float, float]

@dataclass
class Road:
    """
    Represents a road segment in local map coordinates.

    Attributes:
        points_m (List[Point3D]): List of 3D points (x, y, z) in meters, defining the road polyline.
        width (float): Road width in meters.
        border_width (float): Width of the road border in meters. Defaults to 0.0.
        border_height (float): Height of the road border in meters. Defaults to 0.0.
        kind (str): Road surface type (e.g., "asphalt", "gravel"). Defaults to "asphalt".
    """

    points_m: List[Point3D]
    width: float
    border_width: float = 0.0
    border_height: float = 0.0
    kind: str = "asphalt"
    name: Optional[str] = None
    is_bridge: bool = False

    def __post_init__(self):
        """
        Validates the road data after initialization.

        Raises:
            ValueError: If points_m is not a list of at least 2 points,
                        if width is not positive,
                        if any point coordinate is not finite,
                        or if the polyline length is zero.
        """
        if not isinstance(self.points_m, list) or len(self.points_m) < 2:
            raise ValueError("Road.points_m must contain at least 2 points")
        if not (self.width > 0):
            raise ValueError("Road.width must be > 0")
        for (x, y, z) in self.points_m:
            if not all(map(math.isfinite, (x, y, z))):
                raise ValueError("All point coordinates must be finite")
        length = 0.0
        for (x0, y0, _), (x1, y1, __) in zip(self.points_m, self.points_m[1:]):
            length += math.hypot(x1 - x0, y1 - y0)
        if length == 0.0:
            raise ValueError("Road polyline length must be > 0")

    def to_tobj_string(self) -> str:
        """
        Serializes the road segment to a string in .tobj format.

        Returns:
            str: The road segment as a formatted string for .tobj export.
        """
        points_str = " ".join([f"{x:.3f} {y:.3f} {z:.3f}" for x, y, z in self.points_m])
        return (
            f"width {self.width:.2f} "
            f"border_width {self.border_width:.2f} "
            f"border_height {self.border_height:.2f} "
            f"type {self.kind} "
            f"points {points_str}"
        )
