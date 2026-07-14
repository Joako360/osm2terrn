from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from osm2terrn.domain.entities.base import DomainEntity
from osm2terrn.domain.value_objects import Point2D, Polygon, Polyline


@dataclass(slots=True)
class Road(DomainEntity):
    """A road feature represented in local projected coordinates."""

    geometry: Polyline
    width: float | None = None
    surface: str | None = None


@dataclass(slots=True)
class Building(DomainEntity):
    """A building footprint that is independent of any GIS library."""

    geometry: Polygon | Polyline
    height: float | None = None


@dataclass(slots=True)
class Railway(DomainEntity):
    """A railway track represented as a polyline."""

    geometry: Polyline
    electrified: bool | None = None


@dataclass(slots=True)
class WaterBody(DomainEntity):
    """A water feature represented as a polygon or polyline."""

    geometry: Polygon | Polyline
    flow: str | None = None


@dataclass(slots=True)
class VegetationArea(DomainEntity):
    """A vegetation area footprint."""

    geometry: Polygon
    vegetation_type: str | None = None


@dataclass(slots=True)
class TerrainRegion(DomainEntity):
    """A terrain region used by terrain generation workflows."""

    geometry: Polygon
    elevation: float | None = None


@dataclass(slots=True)
class Intersection(DomainEntity):
    """An intersection point between multiple road segments."""

    location: Point2D


@dataclass(slots=True)
class RoadSegment(DomainEntity):
    """A segment of a road graph used by procedural generation."""

    geometry: Polyline
    start_node: Point2D
    end_node: Point2D
    road_id: str | None = None
