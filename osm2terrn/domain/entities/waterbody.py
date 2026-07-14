from dataclasses import dataclass
from typing import Any
from osm2terrn.domain.value_objects import Polygon


@dataclass(slots=True)
class WaterBody:
    id: str
    geometry: Polygon
    water_type: str
    tags: dict[str, Any]