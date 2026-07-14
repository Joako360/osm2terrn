from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Polygon as ShapelyPolygon

from osm2terrn.domain.adapters.osmnx_to_buildings import geodataframe_to_buildings


def test_geodataframe_to_buildings_creates_domain_entities() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["Tower"], "height": [30.0]},
        geometry=[ShapelyPolygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])],
        crs="EPSG:4326",
    )

    buildings = geodataframe_to_buildings(gdf)

    assert len(buildings) == 1
    assert buildings[0].height == 30.0
    assert buildings[0].metadata["name"] == "Tower"
