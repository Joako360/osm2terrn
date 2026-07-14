from __future__ import annotations

from enum import Enum


class FeatureKind(str, Enum):
    """High-level classification for domain entities."""

    ROAD = "road"
    BUILDING = "building"
    RAILWAY = "railway"
    WATER_BODY = "water_body"
    VEGETATION = "vegetation"
    TERRAIN_REGION = "terrain_region"
    INTERSECTION = "intersection"
