from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pytest
from pyproj import CRS, Transformer
from shapely.geometry import LineString

from osm2terrn.adapters import coordinate_transform
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.config.models import ProjectConfig
from osm2terrn.data import osm_data_handler
from osm2terrn.data.street_network import StreetNetworkResult
from osm2terrn.domain.adapters import osmnx_to_map, osmnx_to_roads
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.processing.network import road_network_export
from osm2terrn.processing.orchestrator import _export_roads
from osm2terrn.processing.roads import road_elevation


class MemoryCache:
    def __init__(self, *, invalid: bool = False) -> None:
        self.value = None
        self.invalid = invalid

    def build_key(self, *_args, **_kwargs) -> str:
        return "street-bundle"

    def get(self, **_kwargs):
        if self.invalid:
            raise ValueError("corrupt cache payload")
        return self.value

    def put(self, *, value, **_kwargs) -> None:
        self.value = (value, CacheMetadata())


def make_graph(*, crs: str = "EPSG:4326", elevation: bool = False) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = crs
    node_a = {"x": -58.52, "y": -34.76}
    node_b = {"x": -58.50, "y": -34.74}
    if elevation:
        node_a["elevation"] = 12.0
        node_b["elevation"] = 13.0
    graph.add_node(1, **node_a)
    graph.add_node(2, **node_b)
    graph.add_edge(
        1,
        2,
        key=4,
        geometry=LineString([(-58.52, -34.76), (-58.51, -34.75), (-58.50, -34.74)]),
        highway="residential",
        bridge=False,
        name="Main Street",
    )
    return graph


def test_transform_graph_requires_crs_and_preserves_canonical_graph(monkeypatch) -> None:
    graph = make_graph()
    original_coords = (graph.nodes[1]["x"], graph.nodes[1]["y"])

    transformed = coordinate_transform.transform_graph(graph, "EPSG:3857")

    assert transformed.graph["crs"] == CRS.from_epsg(3857)
    assert transformed.nodes[1]["x"] != pytest.approx(original_coords[0])
    assert (graph.nodes[1]["x"], graph.nodes[1]["y"]) == original_coords
    assert graph.graph["crs"] == "EPSG:4326"
    assert transformed.edges[1, 2, 4]["name"] == "Main Street"
    expected_geometry_start = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform(
        -58.52, -34.76
    )
    assert tuple(transformed.edges[1, 2, 4]["geometry"].coords[0]) == pytest.approx(expected_geometry_start)

    graph.graph.pop("crs")
    with pytest.raises(ValueError, match="Graph CRS is required"):
        coordinate_transform.transform_graph(graph, "EPSG:3857")


def test_transform_graph_propagates_transform_failure_without_relabeling(monkeypatch) -> None:
    graph = make_graph()

    class FailingTransformer:
        def transform(self, *_args, **_kwargs):
            raise ValueError("synthetic transform failure")

    monkeypatch.setattr(coordinate_transform.Transformer, "from_crs", lambda *_args, **_kwargs: FailingTransformer())

    with pytest.raises(ValueError, match="synthetic transform failure"):
        coordinate_transform.transform_graph(graph, "EPSG:3857")

    assert graph.graph["crs"] == "EPSG:4326"
    assert graph.nodes[1]["x"] == pytest.approx(-58.52)


def test_graph_to_mapdata_gdf_transforms_coordinates_and_preserves_edge_attributes(monkeypatch) -> None:
    source_crs = CRS.from_epsg(3857)
    to_projected = Transformer.from_crs("EPSG:4326", source_crs, always_xy=True)
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = source_crs
    first = to_projected.transform(-58.52, -34.76)
    second = to_projected.transform(-58.50, -34.74)
    graph.add_node(1, x=first[0], y=first[1])
    graph.add_node(2, x=second[0], y=second[1])
    edge_geometry = LineString([first, ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2), second])
    graph.add_edge(
        1,
        2,
        key=7,
        geometry=edge_geometry,
        highway="primary",
        bridge=True,
        name="Main Street",
    )

    roads_gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)

    assert CRS.from_user_input(roads_gdf.crs) == CRS.from_epsg(4326)
    assert list(roads_gdf.geometry.iloc[0].coords)[0] == pytest.approx((-58.52, -34.76))
    assert len(roads_gdf.geometry.iloc[0].coords) == 3
    assert roads_gdf.iloc[0]["highway"] == "primary"
    assert bool(roads_gdf.iloc[0]["bridge"])
    assert roads_gdf.iloc[0]["name"] == "Main Street"
    assert roads_gdf.iloc[0]["key"] == 7
    assert CRS.from_user_input(graph.graph["crs"]) == source_crs
    assert graph.edges[1, 2, 7]["geometry"].equals(edge_geometry)

    class NoCache:
        def build_key(self, *_args, **_kwargs):
            return "unused"

        def get(self, **_kwargs):
            return None

        def put(self, **_kwargs):
            return None

    monkeypatch.setattr(osmnx_to_roads, "get_cache_manager", lambda: NoCache())
    monkeypatch.setattr(osmnx_to_map, "get_cache_manager", lambda: NoCache())
    map_data = osmnx_to_map.build_mapdata_from_pipeline_context(
        bounds=BoundingBox(-59, -35, -58, -34, crs="EPSG:4326"),
        place="Test Area",
        roads_gdf=roads_gdf,
    )
    assert map_data.coordinate_system == "EPSG:4326"
    assert len(map_data.roads) == 1
    assert map_data.roads[0].geometry.points[0].x == pytest.approx(-58.52)
    assert map_data.roads[0].metadata["osm_attributes"]["highway"] == "primary"
    assert bool(map_data.roads[0].metadata["osm_attributes"]["bridge"])

    with pytest.raises(ValueError, match="EPSG:4326"):
        osmnx_to_map.build_mapdata_from_pipeline_context(
            roads_gdf=roads_gdf.to_crs("EPSG:3857")
        )


def test_graph_to_mapdata_rejects_unknown_crs() -> None:
    graph = make_graph(crs="not-a-crs")
    with pytest.raises(Exception):
        osmnx_to_roads.graph_to_roads_geodataframe(graph)


def test_edges_to_lines_preserves_source_coordinates_and_crs() -> None:
    from osm2terrn.data.osm_loader import edges_to_lines

    graph = make_graph()
    original_geometry = graph.edges[1, 2, 4]["geometry"].wkb
    lines, source_crs = edges_to_lines(graph)
    assert source_crs == CRS.from_epsg(4326)
    assert lines[0][0].length < 1.0
    assert list(lines[0][0].coords) == list(graph.edges[1, 2, 4]["geometry"].coords)
    assert graph.edges[1, 2, 4]["geometry"].wkb == original_geometry


@pytest.mark.parametrize(
    ("case", "expected_status", "cache_invalid"),
    [
        ("available", "available", False),
        ("empty", "empty", False),
        ("failed", "failed", False),
        ("available", "available", True),
    ],
)
def test_bbox_acquisition_records_distinct_street_states(monkeypatch, case, expected_status, cache_invalid) -> None:
    cache = MemoryCache(invalid=cache_invalid)
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: cache)
    monkeypatch.setattr(osm_data_handler, "map_geometries", {})
    monkeypatch.setattr(osm_data_handler, "networks", {"roads": None})
    graph_calls = []

    def fake_graph_from_bbox(*_args, **_kwargs):
        graph_calls.append(True)
        if case == "failed":
            raise RuntimeError("synthetic provider failure")
        if case == "empty":
            empty = nx.MultiDiGraph()
            empty.graph["crs"] = "EPSG:4326"
            empty.add_node(1, x=-58.52, y=-34.76)
            return empty
        return make_graph()

    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", fake_graph_from_bbox)

    bundle = osm_data_handler.download_data_from_bbox((-58.53, -34.77, -58.49, -34.73))

    assert isinstance(bundle["roads"], StreetNetworkResult)
    assert bundle["roads"].status == expected_status
    assert len(graph_calls) == 1
    if cache_invalid:
        assert bundle["roads"].source == "cache_recovered"
    if case == "failed":
        assert "RuntimeError" in bundle["roads"].diagnostic
    if case == "available":
        assert bundle["roads"].graph.number_of_edges() == 1
        assert CRS.from_user_input(bundle["roads"].graph_crs) == CRS.from_user_input(bundle["roads"].graph.graph["crs"])


def test_bbox_acquisition_marks_roads_not_requested(monkeypatch) -> None:
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: MemoryCache())
    monkeypatch.setattr(osm_data_handler, "map_geometries", {})
    monkeypatch.setattr(osm_data_handler, "networks", {})
    bundle = osm_data_handler.download_data_from_bbox((-58.53, -34.77, -58.49, -34.73))
    assert bundle["roads"].status == "not_requested"
    assert bundle["roads"].source == "none"


def test_node_elevation_sampler_uses_supplied_graph_without_place_reload(monkeypatch) -> None:
    graph = make_graph(elevation=True)
    loader_calls = []

    def unexpected_reload(**_kwargs):
        loader_calls.append(True)
        raise AssertionError("a supplied canonical graph must not be reloaded")

    monkeypatch.setattr("osm2terrn.data.osm_loader.load_graph", unexpected_reload)

    class FakeTree:
        def __init__(self, coordinates):
            self.coordinates = coordinates

    monkeypatch.setattr(
        "importlib.import_module",
        lambda name: type("ScipySpatial", (), {"cKDTree": FakeTree}) if name == "scipy.spatial" else __import__(name),
    )
    sampler = road_elevation.build_node_elevation_sampler("Named Place", "drive", True, graph=graph)
    assert sampler is not None
    assert len(loader_calls) == 0
    assert sampler[1].tolist() == [12.0, 13.0]


def test_graph_road_builder_uses_configured_output_from_another_working_directory(
    monkeypatch, tmp_path: Path
) -> None:
    graph = make_graph()
    captured = {}
    work_dir = tmp_path / "work"
    output_dir = tmp_path / "configured-output"
    work_dir.mkdir()
    output_dir.mkdir()
    monkeypatch.chdir(work_dir)
    monkeypatch.setattr(
        road_network_export._PROGRAM_CONFIG.paths,
        "output_dir",
        output_dir,
    )
    monkeypatch.setattr(road_network_export, "load_graph", lambda **_kwargs: pytest.fail("unexpected place reload"))
    monkeypatch.setattr(road_network_export, "build_dem_sampler", lambda *_args: None)
    monkeypatch.setattr(
        road_network_export,
        "build_node_elevation_sampler",
        lambda place, network_type, simplify, graph: captured.setdefault("graph", graph),
    )
    monkeypatch.setattr(road_network_export, "sample_segment_elevation", lambda local_xz, **_kwargs: np.zeros(len(local_xz)))
    monkeypatch.setattr(road_network_export, "_resolve_target_bounds_local", lambda **_kwargs: (0.0, 0.0, 1.0, 1.0))

    output_path = road_network_export.build_roads_from_graph(
        graph,
        origin_lon=-58.51,
        origin_lat=-34.75,
        place="Test Area",
        tobj_prefix="synthetic",
    )

    assert captured["graph"] is graph
    assert Path(output_path).is_file()
    assert Path(output_path).parent == output_dir
    assert not (work_dir / "synthetic_roads.tobj").exists()
    assert "begin_procedural_roads" in Path(output_path).read_text(encoding="utf-8")


def test_place_road_builder_forwards_configured_output_dir(monkeypatch, tmp_path: Path) -> None:
    graph = make_graph()
    captured = {}
    monkeypatch.setattr(road_network_export, "load_graph", lambda **_kwargs: graph)
    monkeypatch.setattr(
        road_network_export,
        "build_roads_from_graph",
        lambda **kwargs: captured.update(kwargs) or "roads.tobj",
    )

    output_path = road_network_export.build_roads_from_place(
        place="Test Area",
        origin_lon=-58.51,
        origin_lat=-34.75,
        output_dir=str(tmp_path),
    )

    assert output_path == "roads.tobj"
    assert captured["output_dir"] == str(tmp_path)


def test_include_roads_gate_and_graph_export_status(monkeypatch) -> None:
    from osm2terrn.processing import orchestrator

    class FakeMapData:
        def __init__(self):
            self.metadata = {}

    domain_map = FakeMapData()
    graph = make_graph()
    result = StreetNetworkResult(status="available", graph=graph, graph_crs="EPSG:4326")
    monkeypatch.setattr(orchestrator, "build_roads_from_graph", lambda **_kwargs: "roads.tobj")

    assert _export_roads(
        "Test Area", -58.51, -34.75, 0.0, BoundingBox(-59, -35, -58, -34, crs="EPSG:4326"),
        domain_map, result, False,
    ) is None
    assert domain_map.metadata["road_export_status"] == "disabled"
    assert not domain_map.metadata["roads_exported"]

    path = _export_roads(
        "Test Area", -58.51, -34.75, 0.0, BoundingBox(-59, -35, -58, -34, crs="EPSG:4326"),
        domain_map, result, True,
    )
    assert path == "roads.tobj"
    assert domain_map.metadata["road_acquisition_status"] == "available"
    assert domain_map.metadata["road_export_status"] == "exported"
    assert domain_map.metadata["roads_exported"]


def test_missing_source_and_export_failure_are_recorded(monkeypatch) -> None:
    from osm2terrn.processing import orchestrator

    class FakeMapData:
        def __init__(self):
            self.metadata = {}

    bounds = BoundingBox(-59, -35, -58, -34, crs="EPSG:4326")
    missing_map = FakeMapData()
    assert _export_roads("Test Area", 0.0, 0.0, 0.0, bounds, missing_map, None, True) is None
    assert missing_map.metadata["road_acquisition_status"] == "missing"
    assert missing_map.metadata["road_export_status"] == "skipped"

    graph = make_graph()
    result = StreetNetworkResult(status="available", graph=graph, graph_crs="EPSG:4326")
    failed_map = FakeMapData()
    monkeypatch.setattr(
        orchestrator,
        "build_roads_from_graph",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic writer failure")),
    )
    assert _export_roads("Test Area", 0.0, 0.0, 0.0, bounds, failed_map, result, True) is None
    assert failed_map.metadata["road_processing_status"] == "failed"
    assert failed_map.metadata["road_export_status"] == "failed"
    assert failed_map.metadata["roads_exported"] is False


def test_export_include_roads_setting_skips_conversion_and_export(monkeypatch, tmp_path: Path) -> None:
    from osm2terrn.processing import orchestrator

    graph = make_graph()
    result = StreetNetworkResult(status="available", graph=graph, graph_crs="EPSG:4326")
    captured_mapdata = []
    monkeypatch.setattr(orchestrator, "_PROJECT_CONFIG", ProjectConfig(export=ProjectConfig().export))
    orchestrator._PROJECT_CONFIG.export.include_roads = False
    monkeypatch.setattr(orchestrator, "_get_output_dir", lambda: str(tmp_path))
    monkeypatch.setattr(orchestrator, "_export_heightmap_textures", lambda **_kwargs: ("height.png", "ground.png", {"min_elevation": 0.0, "max_elevation": 1.0, "elevation_range": 1.0}))
    monkeypatch.setattr(
        orchestrator,
        "build_mapdata_from_pipeline_context",
        lambda **kwargs: captured_mapdata.append(kwargs) or type("Map", (), {"roads": [], "buildings": [], "metadata": kwargs["metadata"]})(),
    )
    monkeypatch.setattr(orchestrator, "build_roads_from_graph", lambda **_kwargs: pytest.fail("roads must be disabled"))
    monkeypatch.setattr(orchestrator, "export_paged_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_global_otc", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "export_terrn2_entrypoint", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "_write_domain_objects_manifest", lambda *_args, **_kwargs: None)

    orchestrator.export_terrain_assets(
        "Test Area",
        BoundingBox(-59, -35, -58, -34, crs="EPSG:4326"),
        road_network=result,
    )

    assert captured_mapdata[0]["roads_gdf"] is None
    assert captured_mapdata[0]["metadata"]["road_mapdata_status"] == "disabled"
