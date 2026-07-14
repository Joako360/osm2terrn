from dataclasses import dataclass
from typing import Any
from osm2terrn.domain.value_objects import Polyline


@dataclass(slots=True)
class Road:
    id: str
    geometry: Polyline
    highway: str
    lanes: int
    width: float
    surface: str | None
    bridge: bool
    tunnel: bool
    oneway: bool
    maxspeed: float | None
    tags: dict[str, Any]