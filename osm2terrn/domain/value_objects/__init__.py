from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any


@dataclass(slots=True)
class Point2D:
    """Two-dimensional point expressed in local projected coordinates.

    Args:
        x: Horizontal coordinate in meters.
        y: Vertical coordinate in meters.
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        self._validate_coordinate(self.x, "x")
        self._validate_coordinate(self.y, "y")

    @staticmethod
    def _validate_coordinate(value: float, name: str) -> None:
        if not isfinite(value):
            raise ValueError(f"{name} must be a finite number")

    def to_tuple(self) -> tuple[float, float]:
        """Return the point as a tuple of coordinates."""
        return (self.x, self.y)


@dataclass(slots=True)
class Point3D:
    """Three-dimensional point used by terrain and elevation workflows."""

    x: float
    y: float
    z: float = 0.0

    def __post_init__(self) -> None:
        self._validate_coordinate(self.x, "x")
        self._validate_coordinate(self.y, "y")
        self._validate_coordinate(self.z, "z")

    @staticmethod
    def _validate_coordinate(value: float, name: str) -> None:
        if not isfinite(value):
            raise ValueError(f"{name} must be a finite number")

    def to_tuple(self) -> tuple[float, float, float]:
        """Return the point as a tuple of coordinates including elevation."""
        return (self.x, self.y, self.z)


@dataclass(slots=True)
class Polyline:
    """An ordered sequence of 2D points representing a line geometry."""

    points: tuple[Point2D, ...]

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError("Polyline requires at least one point")
        if not all(isinstance(point, Point2D) for point in self.points):
            raise TypeError("Polyline points must be Point2D instances")


@dataclass(slots=True)
class Polygon:
    """A closed polygon defined by an ordered set of 2D points."""

    points: tuple[Point2D, ...]

    def __post_init__(self) -> None:
        if len(self.points) < 3:
            raise ValueError("Polygon requires at least three points")
        if not all(isinstance(point, Point2D) for point in self.points):
            raise TypeError("Polygon points must be Point2D instances")


@dataclass(slots=True, init=False)
class BoundingBox:
    """Axis-aligned rectangular bounding box in local projected coordinates."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    crs: str | None = field(default=None)
    is_projected: bool = field(default=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if len(args) == 1 and isinstance(args[0], BoundingBox):
            src = args[0]
            self.min_x = float(src.min_x)
            self.min_y = float(src.min_y)
            self.max_x = float(src.max_x)
            self.max_y = float(src.max_y)
            self.crs = getattr(src, "crs", None)
            self.is_projected = bool(getattr(src, "is_projected", False))
            return

        if len(args) == 1 and isinstance(args[0], dict):
            data = args[0]
            min_x = data.get("min_x", data.get("west"))
            min_y = data.get("min_y", data.get("south"))
            max_x = data.get("max_x", data.get("east"))
            max_y = data.get("max_y", data.get("north"))
        elif len(args) == 1 and isinstance(args[0], (list, tuple)) and len(args[0]) == 4:
            min_x, min_y, max_x, max_y = args[0]
        elif len(args) == 4:
            min_x, min_y, max_x, max_y = args
        elif len(args) == 0:
            min_x = kwargs.pop("min_x", None)
            min_y = kwargs.pop("min_y", None)
            max_x = kwargs.pop("max_x", None)
            max_y = kwargs.pop("max_y", None)
        else:
            raise TypeError("BoundingBox accepts either (min_x, min_y, max_x, max_y) or a 4-item bounds sequence")

        self.crs = kwargs.pop("crs", None)
        self.is_projected = bool(kwargs.pop("is_projected", False))
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"Unexpected keyword arguments: {unexpected}")

        self.min_x = float(min_x)
        self.min_y = float(min_y)
        self.max_x = float(max_x)
        self.max_y = float(max_y)
        self._validate()

    def _validate(self) -> None:
        for name, value in (("min_x", self.min_x), ("min_y", self.min_y), ("max_x", self.max_x), ("max_y", self.max_y)):
            if not isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if self.min_x >= self.max_x or self.min_y >= self.max_y:
            raise ValueError("BoundingBox minima must be smaller than the maxima")

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> Point2D:
        return Point2D((self.min_x + self.max_x) / 2.0, (self.min_y + self.max_y) / 2.0)

    @property
    def west(self) -> float:
        return self.min_x

    @property
    def south(self) -> float:
        return self.min_y

    @property
    def east(self) -> float:
        return self.max_x

    @property
    def north(self) -> float:
        return self.max_y

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def to_tuple(self) -> tuple[float, float, float, float]:
        return self.bounds

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "crs": self.crs,
            "is_projected": self.is_projected,
        }

    def contains(self, point: Point2D) -> bool:
        return self.min_x <= point.x <= self.max_x and self.min_y <= point.y <= self.max_y

    def reproject(self, to_crs: str) -> "BoundingBox":
        return BoundingBox(self.min_x, self.min_y, self.max_x, self.max_y, crs=to_crs, is_projected=False)


__all__ = [
    "BoundingBox",
    "Point2D",
    "Point3D",
    "Polygon",
    "Polyline",
]
