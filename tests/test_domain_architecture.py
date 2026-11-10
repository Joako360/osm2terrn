from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import LineString

from osm2terrn.domain import (
    BoundingBox,
    Building,
    MapData,
    Point2D,
    Point3D,
    Polyline,
    Road,
)
from osm2terrn.domain.adapters.osmnx import geodataframe_to_roads
from osm2terrn.domain.adapters.osmnx_to_map import build_mapdata_from_pipeline_context


def test_value_objects_validate_and_expose_helpers() -> None:
    point = Point2D(1.0, 2.0)
    assert point.to_tuple() == (1.0, 2.0)

    point3 = Point3D(1.0, 2.0, 3.0)
    assert point3.to_tuple() == (1.0, 2.0, 3.0)

    bbox = BoundingBox(0.0, 0.0, 10.0, 5.0)
    assert bbox.width == 10.0
    assert bbox.height == 5.0
    assert bbox.center == Point2D(5.0, 2.5)

    with pytest.raises(ValueError):
        BoundingBox(2.0, 3.0, 1.0, 2.0)


def test_domain_entities_keep_metadata_and_mapdata_aggregates() -> None:
    road = Road(
        id="road-1",
        geometry=Polyline((Point2D(0.0, 0.0), Point2D(10.0, 0.0))),
        width=6.0,
        metadata={"osm:highway": "residential"},
    )
    building = Building(
        id="building-1",
        geometry=Polyline((Point2D(0.0, 0.0), Point2D(2.0, 0.0), Point2D(2.0, 2.0), Point2D(0.0, 2.0))),
        height=12.0,
    )

    map_data = MapData(
        roads=[road],
        buildings=[building],
        bounding_box=BoundingBox(0.0, 0.0, 10.0, 10.0),
        coordinate_system="EPSG:3857",
    )

    assert map_data.roads[0].metadata["osm:highway"] == "residential"
    assert map_data.buildings[0].height == 12.0


def test_osmnx_adapter_converts_geodataframe_to_domain() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["Main Street"]},
        geometry=[LineString([(0.0, 0.0), (1.0, 1.0)])],
        crs="EPSG:4326",
    )

    roads = geodataframe_to_roads(gdf)

    assert len(roads) == 1
    assert isinstance(roads[0].geometry, Polyline)
    assert roads[0].geometry.points[0] == Point2D(0.0, 0.0)
    assert roads[0].metadata["source"] == "osmnx"


def test_pipeline_adapter_builds_mapdata_from_bounds_and_roads() -> None:
    bounds = gpd.GeoDataFrame(
        geometry=[LineString([(0.0, 0.0), (2.0, 2.0)])],
        crs="EPSG:4326",
    )
    roads_gdf = gpd.GeoDataFrame(
        {"name": ["Main Street"]},
        geometry=[LineString([(0.0, 0.0), (1.0, 1.0)])],
        crs="EPSG:4326",
    )

    map_data = build_mapdata_from_pipeline_context(
        bounds=bounds,
        place="Test City",
        roads_gdf=roads_gdf,
    )

    assert map_data.bounding_box is not None
    assert map_data.bounding_box.width > 0.0
    assert len(map_data.roads) == 1
    assert map_data.metadata["place"] == "Test City"
