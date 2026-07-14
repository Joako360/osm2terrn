from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from osm2terrn.domain.entities.features import (
    Building,
    Intersection,
    Railway,
    Road,
    TerrainRegion,
    VegetationArea,
    WaterBody,
)
from osm2terrn.domain.value_objects import BoundingBox


@dataclass(slots=True)
class MapData:
    """The aggregate root representing the complete state of a map."""

    roads: list[Road] = field(default_factory=list)
    buildings: list[Building] = field(default_factory=list)
    railways: list[Railway] = field(default_factory=list)
    waterways: list[WaterBody] = field(default_factory=list)
    vegetation: list[VegetationArea] = field(default_factory=list)
    terrain_regions: list[TerrainRegion] = field(default_factory=list)
    intersections: list[Intersection] = field(default_factory=list)
    bounding_box: BoundingBox | None = None
    coordinate_system: str = "EPSG:4326"
    elevation_model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)