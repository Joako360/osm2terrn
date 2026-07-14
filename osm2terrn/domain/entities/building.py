from dataclasses import dataclass
from typing import Any
from osm2terrn.domain.value_objects import Polygon


@dataclass(slots=True)
class Building:
    id: str
    footprint: Polygon
    levels: int | None
    height: float | None
    roof_shape: str | None
    material: str | None
    tags: dict[str, Any]