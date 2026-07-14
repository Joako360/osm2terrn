from __future__ import annotations

import importlib
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon as ShapelyPolygon

from osm2terrn.domain.entities import Building, MapData, Road
from osm2terrn.domain.value_objects import BoundingBox, Point2D, Polyline


orchestrator = importlib.import_module("osm2terrn.processing.orchestrator")
export_terrain_assets = orchestrator.export_terrain_assets


def test_export_terrain_assets_populates_domain_state(monkeypatch) -> None:
    calls = []

    def fake_heightmap(bounds, heightmap_path=None, groundmap_path=None, elevation_data=None):
        calls.append("heightmap")
        return {"min_elevation": 0.0, "max_elevation": 10.0, "elevation_range": 10.0}

    def fake_roads(*args, **kwargs):
        calls.append("roads")
        return "output/test_roads.tobj"

    domain_map = MapData(
        roads=[
            Road(
                id="road-1",
                geometry=Polyline((Point2D(0.0, 0.0), Point2D(1.0, 1.0))),
                width=7.0,
                surface="road",
            )
        ],
        buildings=[
            Building(
                id="building-1",
                geometry=Polyline((Point2D(0.0, 0.0), Point2D(1.0, 0.0), Point2D(1.0, 1.0))),
                height=12.0,
            )
        ],
    )

    monkeypatch.setattr(orchestrator, "generate_heightmap_n_texture", fake_heightmap)
    monkeypatch.setattr(orchestrator, "build_roads_from_place", fake_roads)
    monkeypatch.setattr(orchestrator, "build_mapdata_from_pipeline_context", lambda **kwargs: domain_map)
    monkeypatch.setattr(orchestrator, "export_paged_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_global_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_terrn2_entrypoint", lambda *args, **kwargs: None)

    bounds = gpd.GeoDataFrame(
        geometry=[ShapelyPolygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])],
        crs="EPSG:4326",
    )
    bounds._buildings_gdf = gpd.GeoDataFrame(
        {"name": ["Tower"]},
        geometry=[ShapelyPolygon([(0.1, 0.1), (0.3, 0.1), (0.3, 0.3), (0.1, 0.3)])],
        crs="EPSG:4326",
    )

    result = export_terrain_assets("Test City", bounds=bounds, origin_lon=1.0, origin_lat=2.0)

    assert result["roads_tobj"] == "output/test_roads.tobj"
    assert "heightmap" in calls
    assert "roads" in calls
    assert Path(result["tobj"]).read_text(encoding="utf-8") .count("// roads=1") == 1
    assert "// buildings=1" in Path(result["tobj"]).read_text(encoding="utf-8")


def test_export_terrain_assets_accepts_domain_bounds(monkeypatch) -> None:
    calls = []

    def fake_heightmap(bounds, heightmap_path=None, groundmap_path=None, elevation_data=None):
        calls.append("heightmap")
        return {"min_elevation": 0.0, "max_elevation": 10.0, "elevation_range": 10.0}

    monkeypatch.setattr(orchestrator, "generate_heightmap_n_texture", fake_heightmap)
    monkeypatch.setattr(orchestrator, "build_roads_from_place", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "build_mapdata_from_pipeline_context", lambda **kwargs: MapData())
    monkeypatch.setattr(orchestrator, "export_paged_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_global_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_terrn2_entrypoint", lambda *args, **kwargs: None)

    result = export_terrain_assets(
        "Test City",
        bounds=BoundingBox(0.0, 0.0, 1.0, 1.0),
        origin_lon=1.0,
        origin_lat=2.0,
    )

    assert result["heightmap"]
    assert "heightmap" in calls


def test_export_terrain_assets_skips_roads_when_domain_has_no_roads(monkeypatch) -> None:
    calls = []

    def fake_heightmap(bounds, heightmap_path=None, groundmap_path=None, elevation_data=None):
        calls.append("heightmap")
        return {"min_elevation": 0.0, "max_elevation": 10.0, "elevation_range": 10.0}

    def fake_roads(*args, **kwargs):
        calls.append("roads")
        return "output/test_roads.tobj"

    monkeypatch.setattr(orchestrator, "generate_heightmap_n_texture", fake_heightmap)
    monkeypatch.setattr(orchestrator, "build_roads_from_place", fake_roads)
    monkeypatch.setattr(orchestrator, "build_mapdata_from_pipeline_context", lambda **kwargs: MapData())
    monkeypatch.setattr(orchestrator, "export_paged_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_global_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_terrn2_entrypoint", lambda *args, **kwargs: None)

    bounds = gpd.GeoDataFrame(
        geometry=[ShapelyPolygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])],
        crs="EPSG:4326",
    )

    result = export_terrain_assets("Test City", bounds=bounds, origin_lon=1.0, origin_lat=2.0)

    assert result["roads_tobj"] is None
    assert calls == ["heightmap"]
