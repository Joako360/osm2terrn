"""Backward-compatible BBox shim backed by the domain BoundingBox value object."""

from __future__ import annotations

from typing import Any

from osm2terrn.domain.adapters.bounds import require_domain_bounding_box
from osm2terrn.domain.value_objects import BoundingBox


class BBox(BoundingBox):
    """Compatibility wrapper that reuses the canonical BoundingBox implementation."""

    def __init__(self, src: Any) -> None:
        bbox_obj = require_domain_bounding_box(src)
        super().__init__(
            bbox_obj.min_x,
            bbox_obj.min_y,
            bbox_obj.max_x,
            bbox_obj.max_y,
            crs=bbox_obj.crs,
            is_projected=bbox_obj.is_projected,
        )

    def as_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        return {
            "west": data["min_x"],
            "south": data["min_y"],
            "east": data["max_x"],
            "north": data["max_y"],
            "crs": data["crs"],
            "is_projected": data["is_projected"],
        }

    def to_geojson(self) -> tuple[float, float, float, float]:
        return self.to_tuple()

    def bbox_tuple(self) -> tuple[float, float, float, float]:
        return self.to_tuple()

    def __repr__(self) -> str:
        return (
            f"BBox(west={self.west}, south={self.south}, east={self.east}, "
            f"north={self.north}, crs={self.crs})"
        )
