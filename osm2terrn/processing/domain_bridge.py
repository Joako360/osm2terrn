from __future__ import annotations

from typing import Any

from osm2terrn.domain.entities import Building, Road
from osm2terrn.domain.value_objects import Point2D, Point3D, Polyline


def road_to_domain_model(road: Any) -> Road:
    """Convert the existing processing Road model into a domain Road entity."""

    points = [Point2D(float(x), float(z)) for x, _, z in road.points_m]
    return Road(
        id=str(id(road)),
        geometry=Polyline(tuple(points)),
        width=float(road.width),
        surface=getattr(road, "type", None),
        metadata={
            "name": getattr(road, "name", None),
            "is_bridge": getattr(road, "is_bridge", False),
            "source": "processing",
        },
    )


def building_to_domain_model(building: Any) -> Building:
    """Convert a processing building-like object into a domain Building entity."""

    if hasattr(building, "footprint"):
        footprint = getattr(building, "footprint")
        if hasattr(footprint, "points"):
            points = [Point2D(float(point.x), float(point.y)) for point in footprint.points]
            geometry = Polyline(tuple(points))
        else:
            geometry = Polyline(tuple())
    else:
        geometry = Polyline(tuple())

    return Building(
        id=str(id(building)),
        geometry=geometry,
        height=getattr(building, "height", None),
        metadata={"source": "processing"},
    )
