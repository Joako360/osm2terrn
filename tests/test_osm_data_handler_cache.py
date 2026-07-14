from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.data import osm_data_handler


def test_download_data_from_bbox_uses_cache(monkeypatch, tmp_path: Path) -> None:
    feature_calls = {"count": 0}
    graph_calls = {"count": 0}

    def fake_features_from_bbox(west, south, east, north, tags):
        feature_calls["count"] += 1
        return gpd.GeoDataFrame({"highway": ["residential"]}, geometry=[Point((west + east) / 2.0, (south + north) / 2.0)], crs="EPSG:4326")

    class _Graph:
        def __init__(self):
            self.nodes = [1]

    def fake_graph_from_bbox(_bbox, network_type, simplify, retain_all, custom_filter):
        graph_calls["count"] += 1
        return _Graph()

    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(osm_data_handler.ox, "features_from_bbox", fake_features_from_bbox)
    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", fake_graph_from_bbox)
    monkeypatch.setattr(osm_data_handler, "transform_gdf_to_ror", lambda gdf, lon, lat: gdf)
    monkeypatch.setattr(osm_data_handler, "transform_graph_to_ror", lambda graph, lon, lat: {"graph": "ok"})

    bbox = (-58.52, -34.76, -58.50, -34.74)
    first = osm_data_handler.download_data_from_bbox(bbox)
    second = osm_data_handler.download_data_from_bbox(bbox)

    assert first.keys() == second.keys()
    assert feature_calls["count"] == len(osm_data_handler.map_geometries)
    assert graph_calls["count"] == len(osm_data_handler.networks)


def test_download_buildings_from_overture_uses_cache(monkeypatch, tmp_path: Path) -> None:
    load_calls = {"count": 0}
    run_calls = {"count": 0}

    class _Udf:
        pass

    def fake_load(url: str):
        load_calls["count"] += 1
        return _Udf()

    def fake_run(udf, parameters):
        run_calls["count"] += 1
        return {
            "geometry": [Point(-58.51, -34.75)],
            "id": ["b1"],
        }

    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(osm_data_handler.fused, "load", fake_load)
    monkeypatch.setattr(osm_data_handler.fused, "run", fake_run)

    bbox = (-58.52, -34.76, -58.50, -34.74)
    gdf_a = osm_data_handler.download_builings_from_overture(bbox)
    gdf_b = osm_data_handler.download_builings_from_overture(bbox)

    assert len(gdf_a) == 1
    assert len(gdf_b) == 1
    assert load_calls["count"] == 1
    assert run_calls["count"] == 1
