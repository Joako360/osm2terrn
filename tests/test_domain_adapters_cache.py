from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import LineString, box

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.domain.adapters import osmnx_to_map
from osm2terrn.domain.adapters import osmnx_to_roads


def _build_roads_gdf() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"name": ["Main"]},
        geometry=[LineString([(0.0, 0.0), (1.0, 1.0)])],
        crs="EPSG:4326",
    )


def _build_buildings_gdf(side_length: float = 1.0) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"name": ["Building"], "height": [12.0]},
        geometry=[box(0.0, 0.0, side_length, side_length)],
        crs="EPSG:4326",
    )


def test_geodataframe_to_roads_uses_cache(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osmnx_to_map, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(osmnx_to_roads, "get_cache_manager", lambda: manager)

    call_count = [0]
    original_iterrows = gpd.GeoDataFrame.iterrows

    def counting_iterrows(self):
        call_count[0] += 1
        return original_iterrows(self)

    monkeypatch.setattr(gpd.GeoDataFrame, "iterrows", counting_iterrows)

    gdf = _build_roads_gdf()
    roads_first = osmnx_to_map.geodataframe_to_roads(gdf)
    roads_second = osmnx_to_map.geodataframe_to_roads(gdf)

    assert len(roads_first) == 1
    assert len(roads_second) == 1
    assert call_count[0] == 1


def test_build_mapdata_from_pipeline_context_uses_cache(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osmnx_to_map, "get_cache_manager", lambda: manager)

    road_calls = {"count": 0}
    original_converter = osmnx_to_map.geodataframe_to_roads

    def counting_converter(gdf):
        road_calls["count"] += 1
        return original_converter(gdf)

    monkeypatch.setattr(osmnx_to_map, "geodataframe_to_roads", counting_converter)

    roads_gdf = _build_roads_gdf()
    first = osmnx_to_map.build_mapdata_from_pipeline_context(
        place="X",
        roads_gdf=roads_gdf,
        buildings_gdf=None,
        metadata={"origin_lon": 1.0},
    )
    second = osmnx_to_map.build_mapdata_from_pipeline_context(
        place="X",
        roads_gdf=roads_gdf,
        buildings_gdf=None,
        metadata={"origin_lon": 1.0},
    )

    assert len(first.roads) == 1
    assert len(second.roads) == 1
    assert road_calls["count"] == 1


def test_build_mapdata_from_pipeline_context_caches_building_data(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osmnx_to_map, "get_cache_manager", lambda: manager)

    building_calls = {"count": 0}
    original_converter = osmnx_to_map.geodataframe_to_buildings

    def counting_converter(gdf):
        building_calls["count"] += 1
        return original_converter(gdf)

    monkeypatch.setattr(osmnx_to_map, "geodataframe_to_buildings", counting_converter)

    first = osmnx_to_map.build_mapdata_from_pipeline_context(
        place="X",
        buildings_gdf=_build_buildings_gdf(),
    )
    second = osmnx_to_map.build_mapdata_from_pipeline_context(
        place="X",
        buildings_gdf=_build_buildings_gdf(side_length=2.0),
    )
    second_cached = osmnx_to_map.build_mapdata_from_pipeline_context(
        place="X",
        buildings_gdf=_build_buildings_gdf(side_length=2.0),
    )

    assert len(first.buildings) == 1
    assert len(second.buildings) == 1
    assert max(point.x for point in second.buildings[0].geometry.points) == 2.0
    assert max(point.x for point in second_cached.buildings[0].geometry.points) == 2.0
    assert building_calls["count"] == 2


def test_build_mapdata_from_pipeline_context_rejects_non_wgs84_buildings() -> None:
    buildings_gdf = _build_buildings_gdf().to_crs("EPSG:3857")

    with pytest.raises(ValueError, match="buildings_gdf.*EPSG:4326"):
        osmnx_to_map.build_mapdata_from_pipeline_context(buildings_gdf=buildings_gdf)
