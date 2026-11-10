from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import networkx as nx
import pytest
from shapely.geometry import Point

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.data import osm_data_handler
from osm2terrn.data.street_network import StreetNetworkResult


def test_download_data_from_bbox_uses_cache(monkeypatch, tmp_path: Path) -> None:
    feature_calls = {"count": 0}
    graph_calls = {"count": 0}

    def fake_features_from_bbox(bbox, tags):
        # Same signature as osmnx 2.x: features_from_bbox(bbox, tags).
        west, south, east, north = bbox
        feature_calls["count"] += 1
        return gpd.GeoDataFrame({"highway": ["residential"]}, geometry=[Point((west + east) / 2.0, (south + north) / 2.0)], crs="EPSG:4326")

    graph = nx.MultiDiGraph()
    graph.graph["crs"] = "EPSG:4326"
    graph.add_node(1, x=-58.52, y=-34.76)
    graph.add_node(2, x=-58.50, y=-34.74)
    graph.add_edge(1, 2, highway="residential")

    def fake_graph_from_bbox(_bbox, network_type, simplify, retain_all, custom_filter):
        graph_calls["count"] += 1
        return graph

    def fake_transform_graph(graph, lon, lat):
        result = graph.copy()
        result.graph["crs"] = "EPSG:4326"
        return result

    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(osm_data_handler.ox, "features_from_bbox", fake_features_from_bbox)
    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", fake_graph_from_bbox)
    monkeypatch.setattr(osm_data_handler, "transform_gdf_to_ror", lambda gdf, lon, lat: gdf)
    monkeypatch.setattr(osm_data_handler, "transform_graph_to_ror", fake_transform_graph)

    bbox = (-58.52, -34.76, -58.50, -34.74)
    first = osm_data_handler.download_data_from_bbox(bbox)
    second = osm_data_handler.download_data_from_bbox(bbox)

    assert first.keys() == second.keys()
    assert feature_calls["count"] == len(osm_data_handler.map_geometries)
    assert graph_calls["count"] == len(osm_data_handler.networks)
    assert isinstance(first["roads"], StreetNetworkResult)
    assert first["roads"].status == "available"
    assert second["roads"].source == "cache"
    for name in osm_data_handler.map_geometries:
        assert first[name] is not None, f"{name} was silently skipped"


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


def _configure_geometry_only_query(monkeypatch, manager, response) -> dict[str, int]:
    calls = {"features": 0}
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(
        osm_data_handler,
        "map_geometries",
        {"buildings": {"building": True}},
    )
    monkeypatch.setattr(osm_data_handler, "networks", {})

    def fake_features(*_args, **_kwargs):
        calls["features"] += 1
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(osm_data_handler.ox, "features_from_bbox", fake_features)
    monkeypatch.setattr(osm_data_handler, "transform_gdf_to_ror", lambda gdf, *_args: gdf)
    return calls


def test_legitimate_empty_geometry_is_cached_with_empty_status(
    monkeypatch, tmp_path: Path
) -> None:
    empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    calls = _configure_geometry_only_query(monkeypatch, manager, empty_gdf)
    bbox = (-58.52, -34.76, -58.50, -34.74)

    first = osm_data_handler.download_data_from_bbox(bbox)
    second = osm_data_handler.download_data_from_bbox(bbox)

    assert first["buildings"] is None
    assert first["acquisition_results"]["buildings"].status == "empty"
    assert second["acquisition_results"]["buildings"].status == "empty"
    assert second["acquisition_results"]["buildings"].source == "cache"
    assert calls["features"] == 1


def test_osmnx_no_matching_features_is_a_valid_empty_result(monkeypatch, tmp_path: Path) -> None:
    empty_response = osm_data_handler.ox._errors.InsufficientResponseError(
        "No matching features in the area"
    )
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    _configure_geometry_only_query(monkeypatch, manager, empty_response)

    result = osm_data_handler.download_data_from_bbox(
        (-58.52, -34.76, -58.50, -34.74)
    )

    assert result["buildings"] is None
    assert result["acquisition_results"]["buildings"].status == "empty"


@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("Server responded: 502 Bad Gateway", "temporary"),
        ("Server responded: 401 Unauthorized", "permanent"),
    ],
)
def test_failed_geometry_is_not_cached_and_can_be_retried(
    monkeypatch, tmp_path: Path, message: str, expected_category: str
) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    error = osm_data_handler.ox._errors.ResponseStatusCodeError(message)
    _configure_geometry_only_query(monkeypatch, manager, error)
    bbox = (-58.52, -34.76, -58.50, -34.74)

    failed = osm_data_handler.download_data_from_bbox(bbox)
    assert failed["buildings"] is None
    assert failed["acquisition_results"]["buildings"].status == "failed"
    assert (
        failed["acquisition_results"]["buildings"].failure_category
        == expected_category
    )
    assert manager.exists(
        namespace=osm_data_handler._OSM_BBOX_CACHE_NAMESPACE,
        key=manager.build_key(
            {
                "bbox": list(bbox),
                "bbox_is_projected": False,
                "bbox_crs": "EPSG:4326",
                "map_geometries": osm_data_handler.map_geometries,
                "networks": {},
                "custom_tags": osm_data_handler.custom_tags,
            },
            provider="osm",
            algorithm_version=osm_data_handler._OSM_BBOX_ALGORITHM_VERSION,
            format_version="3",
            artifact_type="osm_bbox_bundle",
        ),
    ) is False

    successful_gdf = gpd.GeoDataFrame(
        {"id": ["building-1"]},
        geometry=[Point(-58.51, -34.75)],
        crs="EPSG:4326",
    )
    retry_calls = _configure_geometry_only_query(
        monkeypatch, manager, successful_gdf
    )
    recovered = osm_data_handler.download_data_from_bbox(bbox)
    cached = osm_data_handler.download_data_from_bbox(bbox)

    assert recovered["acquisition_results"]["buildings"].status == "available"
    assert cached["acquisition_results"]["buildings"].status == "available"
    assert cached["acquisition_results"]["buildings"].source == "cache"
    assert retry_calls["features"] == 1


def test_road_http_failure_diagnostic_includes_status_and_category(
    monkeypatch, tmp_path: Path
) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    calls = 0

    def fail_with_overpass_502(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise osm_data_handler.ox._errors.ResponseStatusCodeError(
            "Server responded: 502 Bad Gateway"
        )

    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(osm_data_handler, "map_geometries", {})
    monkeypatch.setattr(osm_data_handler, "networks", {"roads": None})
    monkeypatch.setattr(
        osm_data_handler._PROGRAM_CONFIG.osm,
        "overpass_max_attempts",
        1,
    )
    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", fail_with_overpass_502)

    result = osm_data_handler.download_data_from_bbox(
        (-58.52, -34.76, -58.50, -34.74)
    )

    assert calls == 1
    assert result["roads"].status == "failed"
    assert "HTTP 502" in result["roads"].diagnostic
    assert "category=temporary" in result["roads"].diagnostic


def test_version_five_does_not_reuse_legacy_bundle(monkeypatch, tmp_path: Path) -> None:
    bbox = (-58.52, -34.76, -58.50, -34.74)
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    _configure_geometry_only_query(
        monkeypatch,
        manager,
        gpd.GeoDataFrame(geometry=[], crs="EPSG:4326"),
    )
    key_inputs = {
        "bbox": list(bbox),
        "bbox_is_projected": False,
        "bbox_crs": "EPSG:4326",
        "map_geometries": osm_data_handler.map_geometries,
        "networks": {},
        "custom_tags": osm_data_handler.custom_tags,
    }
    legacy_key = manager.build_key(
        key_inputs,
        provider="osm",
        algorithm_version="4",
        format_version="2",
        artifact_type="osm_bbox_bundle",
    )
    serializer = osm_data_handler.PickleSerializer[dict]()
    manager.put(
        namespace=osm_data_handler._OSM_BBOX_CACHE_NAMESPACE,
        key=legacy_key,
        value={"legacy": True},
        serializer=serializer,
    )

    result = osm_data_handler.download_data_from_bbox(bbox)

    assert osm_data_handler._OSM_BBOX_ALGORITHM_VERSION == "5"
    assert result.get("legacy") is None
    assert manager.exists(
        namespace=osm_data_handler._OSM_BBOX_CACHE_NAMESPACE,
        key=legacy_key,
    )


def test_partial_successful_layers_are_cached_and_reused_offline(
    monkeypatch, tmp_path: Path
) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(
        osm_data_handler,
        "map_geometries",
        {
            "buildings": {"building": True},
            "parks": {"leisure": "park"},
            "lakes": {"natural": "water"},
        },
    )
    monkeypatch.setattr(osm_data_handler, "networks", {})
    calls = {"buildings": 0, "parks": 0, "lakes": 0}
    building_data = gpd.GeoDataFrame(
        {"id": ["b1"]},
        geometry=[Point(-58.51, -34.75)],
        crs="EPSG:4326",
    )
    empty_data = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    def fake_features(_bbox, tags):
        layer = next(
            name
            for name, layer_tags in osm_data_handler.map_geometries.items()
            if layer_tags == tags
        )
        calls[layer] += 1
        if layer == "buildings":
            return building_data
        if layer == "parks":
            return empty_data
        raise osm_data_handler.ox._errors.ResponseStatusCodeError(
            "Server responded: 400 Bad Request"
        )

    monkeypatch.setattr(osm_data_handler.ox, "features_from_bbox", fake_features)
    monkeypatch.setattr(osm_data_handler, "transform_gdf_to_ror", lambda gdf, *_args: gdf)

    bbox = (-58.52, -34.76, -58.50, -34.74)
    first = osm_data_handler.download_data_from_bbox(bbox)

    assert first["acquisition_results"]["buildings"].status == "available"
    assert first["acquisition_results"]["parks"].status == "empty"
    assert first["acquisition_results"]["lakes"].status == "failed"
    assert calls == {"buildings": 1, "parks": 1, "lakes": 1}

    second = osm_data_handler.download_data_from_bbox(bbox)

    assert second["acquisition_results"]["buildings"].source == "cache"
    assert second["acquisition_results"]["parks"].source == "cache"
    assert second["acquisition_results"]["lakes"].status == "failed"
    assert calls == {"buildings": 1, "parks": 1, "lakes": 2}

    def fail_if_cached_layer_is_requeried(_bbox, tags):
        if tags in (
            osm_data_handler.map_geometries["buildings"],
            osm_data_handler.map_geometries["parks"],
        ):
            pytest.fail("A successfully cached OSM layer was queried again")
        calls["lakes"] += 1
        return empty_data

    monkeypatch.setattr(
        osm_data_handler.ox,
        "features_from_bbox",
        fail_if_cached_layer_is_requeried,
    )
    third = osm_data_handler.download_data_from_bbox(bbox)

    assert third["acquisition_results"]["buildings"].source == "cache"
    assert third["acquisition_results"]["parks"].source == "cache"
    assert third["acquisition_results"]["lakes"].status == "empty"
    assert calls == {"buildings": 1, "parks": 1, "lakes": 3}

    monkeypatch.setattr(
        osm_data_handler.ox,
        "features_from_bbox",
        lambda *_args, **_kwargs: pytest.fail("Complete cache was not reused"),
    )
    offline = osm_data_handler.download_data_from_bbox(bbox)

    assert offline["acquisition_results"]["buildings"].source == "cache"
    assert offline["acquisition_results"]["parks"].source == "cache"
    assert offline["acquisition_results"]["lakes"].source == "cache"
