from __future__ import annotations

import geopandas as gpd

from osm2terrn.domain.entities import Building
from osm2terrn.domain.value_objects import Point2D, Polyline


def geodataframe_to_buildings(gdf: gpd.GeoDataFrame | None) -> list[Building]:
    """Convert a GeoDataFrame of building geometries into domain entities."""

    if gdf is None or gdf.empty:
        return []

    buildings: list[Building] = []
    for index, row in gdf.iterrows():
        geometry = row.geometry
        if geometry is None:
            continue

        if hasattr(geometry, "geoms"):
            coords: list[tuple[float, float]] = []
            for geom in geometry.geoms:
                if hasattr(geom, "exterior"):
                    coords.extend((float(x), float(y)) for x, y in geom.exterior.coords)
                elif hasattr(geom, "coords"):
                    coords.extend((float(x), float(y)) for x, y in geom.coords)
            if not coords:
                continue
            points = [Point2D(x, y) for x, y in coords]
        elif hasattr(geometry, "exterior"):
            points = [Point2D(float(x), float(y)) for x, y in geometry.exterior.coords]
        elif hasattr(geometry, "coords"):
            points = [Point2D(float(x), float(y)) for x, y in geometry.coords]
        else:
            continue

        buildings.append(
            Building(
                id=str(index),
                geometry=Polyline(tuple(points)) if points else Polyline((Point2D(0.0, 0.0),)),
                height=row.get("height") if isinstance(row.get("height"), (int, float)) else None,
                metadata={"source": "osmnx", "name": row.get("name")},
            )
        )
    return buildings
