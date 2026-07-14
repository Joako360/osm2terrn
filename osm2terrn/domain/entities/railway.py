from dataclasses import dataclass
from osm2terrn.domain.value_objects import Polyline

@dataclass(slots=True)
class Railway:
    id: str
    geometry: Polyline
    railway: str
    electrified: bool
    gauge: int | None