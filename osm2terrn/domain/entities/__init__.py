from __future__ import annotations

from osm2terrn.domain.entities.base import DomainEntity
from osm2terrn.domain.entities.features import (
    Building,
    Intersection,
    Railway,
    Road,
    RoadSegment,
    TerrainRegion,
    VegetationArea,
    WaterBody,
)
from osm2terrn.domain.entities.map_data import MapData

__all__ = [
    "Building",
    "DomainEntity",
    "Intersection",
    "MapData",
    "Railway",
    "Road",
    "RoadSegment",
    "TerrainRegion",
    "VegetationArea",
    "WaterBody",
]
