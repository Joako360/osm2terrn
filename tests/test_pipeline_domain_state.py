from __future__ import annotations

import importlib
from pathlib import Path

import networkx as nx
from shapely.geometry import LineString

from osm2terrn.domain.entities import Building, MapData, Road
from osm2terrn.domain.value_objects import BoundingBox, Point2D, Polyline
from osm2terrn.data.street_network import StreetNetworkResult
from osm2terrn.config.models import ProjectConfig


orchestrator = importlib.import_module("osm2terrn.processing.orchestrator")
export_terrain_assets = orchestrator.export_terrain_assets


def test_export_terrain_assets_populates_domain_state(monkeypatch, tmp_path: Path) -> None:
    calls = []
    mapdata_inputs = []

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
    monkeypatch.setattr(orchestrator, "build_roads_from_graph", fake_roads)
    monkeypatch.setattr(orchestrator, "_PROJECT_CONFIG", ProjectConfig())
    monkeypatch.setattr(orchestrator, "_get_output_dir", lambda: str(tmp_path))
    monkeypatch.setattr(
        orchestrator,
        "build_mapdata_from_pipeline_context",
        lambda **kwargs: mapdata_inputs.append(kwargs) or domain_map,
    )
    monkeypatch.setattr(orchestrator, "export_paged_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_global_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_terrn2_entrypoint", lambda *args, **kwargs: None)

    bounds = BoundingBox(0.0, 0.0, 1.0, 1.0, crs="EPSG:4326", is_projected=False)

    graph = nx.MultiDiGraph()
    graph.graph["crs"] = "EPSG:4326"
    graph.add_node(1, x=1.0, y=2.0)
    graph.add_node(2, x=1.1, y=2.1)
    graph.add_edge(1, 2, geometry=LineString([(1.0, 2.0), (1.1, 2.1)]), highway="residential")
    road_network = StreetNetworkResult(status="available", graph=graph, graph_crs="EPSG:4326")

    result = export_terrain_assets(
        "Test City", bounds=bounds, origin_lon=1.0, origin_lat=2.0, road_network=road_network
    )

    assert result["roads_tobj"] == "output/test_roads.tobj"
    assert "heightmap" in calls
    assert "roads" in calls
    assert mapdata_inputs[0]["roads_gdf"].crs.to_string() == "EPSG:4326"
    assert Path(result["tobj"]).read_text(encoding="utf-8") .count("// roads=1") == 1
    assert "// buildings=1" in Path(result["tobj"]).read_text(encoding="utf-8")


def test_export_terrain_assets_accepts_domain_bounds(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def fake_heightmap(bounds, heightmap_path=None, groundmap_path=None, elevation_data=None):
        calls.append("heightmap")
        return {"min_elevation": 0.0, "max_elevation": 10.0, "elevation_range": 10.0}

    monkeypatch.setattr(orchestrator, "generate_heightmap_n_texture", fake_heightmap)
    monkeypatch.setattr(orchestrator, "_get_output_dir", lambda: str(tmp_path))
    monkeypatch.setattr(orchestrator, "build_roads_from_graph", lambda *args, **kwargs: None)
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


def test_export_terrain_assets_skips_roads_when_domain_has_no_roads(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def fake_heightmap(bounds, heightmap_path=None, groundmap_path=None, elevation_data=None):
        calls.append("heightmap")
        return {"min_elevation": 0.0, "max_elevation": 10.0, "elevation_range": 10.0}

    def fake_roads(*args, **kwargs):
        calls.append("roads")
        return "output/test_roads.tobj"

    monkeypatch.setattr(orchestrator, "generate_heightmap_n_texture", fake_heightmap)
    monkeypatch.setattr(orchestrator, "_get_output_dir", lambda: str(tmp_path))
    monkeypatch.setattr(orchestrator, "build_roads_from_graph", fake_roads)
    monkeypatch.setattr(orchestrator, "build_mapdata_from_pipeline_context", lambda **kwargs: MapData())
    monkeypatch.setattr(orchestrator, "export_paged_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_global_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_terrn2_entrypoint", lambda *args, **kwargs: None)

    bounds = BoundingBox(0.0, 0.0, 1.0, 1.0, crs="EPSG:4326", is_projected=False)

    result = export_terrain_assets("Test City", bounds=bounds, origin_lon=1.0, origin_lat=2.0)

    assert result["roads_tobj"] is None
    assert calls == ["heightmap"]
