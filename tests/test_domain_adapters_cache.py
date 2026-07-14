from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString

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


def test_geodataframe_to_roads_uses_cache(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osmnx_to_roads, "get_cache_manager", lambda: manager)

    call_count = {"iterrows": 0}
    original_iterrows = gpd.GeoDataFrame.iterrows

    def counting_iterrows(self):
        call_count["iterrows"] += 1
        return original_iterrows(self)

    monkeypatch.setattr(gpd.GeoDataFrame, "iterrows", counting_iterrows)

    gdf = _build_roads_gdf()
    roads_first = osmnx_to_roads.geodataframe_to_roads(gdf)
    roads_second = osmnx_to_roads.geodataframe_to_roads(gdf)

    assert len(roads_first) == 1
    assert len(roads_second) == 1
    assert call_count["iterrows"] == 1


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
        metadata={"origin_lon": 1.0},
    )
    second = osmnx_to_map.build_mapdata_from_pipeline_context(
        place="X",
        roads_gdf=roads_gdf,
        metadata={"origin_lon": 1.0},
    )

    assert len(first.roads) == 1
    assert len(second.roads) == 1
    assert road_calls["count"] == 1
