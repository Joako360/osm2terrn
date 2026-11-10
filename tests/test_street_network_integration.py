"""Offline integration tests for the canonical street-graph handoff.

Fixtures are synthetic (no network, no providers, no terrain generation).
They complement ``test_street_network_handoff.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
import pytest
from pyproj import CRS, Transformer
from shapely.geometry import LineString, MultiLineString

from osm2terrn.adapters.coordinate_transform import local_crs_from_lonlat, transform_graph
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cli import commands
from osm2terrn.config.models import ProjectConfig
from osm2terrn.data import osm_data_handler
from osm2terrn.data.acquisition import LayerAcquisitionResult
from osm2terrn.data.street_network import StreetNetworkResult
from osm2terrn.domain.adapters import osmnx_to_map, osmnx_to_roads
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.processing import orchestrator

LON_A, LAT_A = -58.52, -34.76
LON_B, LAT_B = -58.50, -34.74
BBOX = (-58.53, -34.77, -58.49, -34.73)
UTM_21S = "EPSG:32721"


class MemoryCache:
    def __init__(self) -> None:
        self.value = None

    def build_key(self, *_args, **_kwargs) -> str:
        return "street-bundle"

    def get(self, **_kwargs):
        return self.value

    def put(self, *, value, **_kwargs) -> None:
        self.value = (value, CacheMetadata())


class NoCache:
    def build_key(self, *_args, **_kwargs) -> str:
        return "unused"

    def get(self, **_kwargs):
        return None

    def put(self, **_kwargs) -> None:
        return None


def graph_in(crs: str, *, geometry: bool = True, **edge_attrs: Any) -> nx.MultiDiGraph:
    """Two-node graph whose node/edge coordinates are expressed in ``crs``."""
    to_crs = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    a = to_crs.transform(LON_A, LAT_A)
    b = to_crs.transform(LON_B, LAT_B)
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = crs
    graph.add_node(1, x=a[0], y=a[1])
    graph.add_node(2, x=b[0], y=b[1])
    attrs = dict(edge_attrs)
    if geometry:
        mid = ((a[0] + b[0]) / 2 + 1.0, (a[1] + b[1]) / 2 + 1.0)
        attrs["geometry"] = LineString([a, mid, b])
    graph.add_edge(1, 2, key=3, **attrs)
    return graph


def snapshot(graph: nx.MultiDiGraph) -> tuple:
    edges = tuple(
        (u, v, k, tuple((name, value.wkb if hasattr(value, "wkb") else repr(value)) for name, value in sorted(d.items())))
        for u, v, k, d in graph.edges(keys=True, data=True)
    )
    return (
        str(graph.graph.get("crs")),
        tuple((n, tuple(sorted(d.items()))) for n, d in graph.nodes(data=True)),
        edges,
    )


@pytest.fixture
def no_domain_cache(monkeypatch):
    monkeypatch.setattr(osmnx_to_roads, "get_cache_manager", lambda: NoCache())
    monkeypatch.setattr(osmnx_to_map, "get_cache_manager", lambda: NoCache())


def build_map(roads_gdf):
    return osmnx_to_map.build_mapdata_from_pipeline_context(
        bounds=BoundingBox(-59, -35, -58, -34, crs="EPSG:4326"),
        place="Fixture",
        roads_gdf=roads_gdf,
    )


# ----------------------------------------------------------------- Task A


@pytest.mark.parametrize("crs", [UTM_21S, "EPSG:3857"])
def test_projected_graph_is_really_transformed_to_epsg4326(crs, no_domain_cache) -> None:
    graph = graph_in(crs, highway="residential", name="Main Street", bridge=True)
    before = snapshot(graph)

    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)

    assert CRS.from_user_input(gdf.crs) == CRS.from_epsg(4326)
    coords = list(gdf.geometry.iloc[0].coords)
    assert coords[0] == pytest.approx((LON_A, LAT_A), abs=1e-6)
    assert coords[-1] == pytest.approx((LON_B, LAT_B), abs=1e-6)
    assert len(coords) == 3
    # Projected metres must not survive as "degrees".
    assert max(abs(c) for xy in coords for c in xy) < 200
    assert gdf.iloc[0]["highway"] == "residential"
    assert gdf.iloc[0]["name"] == "Main Street"
    assert gdf.iloc[0][["u", "v", "key"]].tolist() == [1, 2, 3]
    assert snapshot(graph) == before

    road = build_map(gdf).roads[0]
    assert road.geometry.points[0].x == pytest.approx(LON_A, abs=1e-6)
    assert road.metadata["osm_attributes"]["name"] == "Main Street"


def test_geographic_graph_keeps_coordinates_and_declares_epsg4326(no_domain_cache) -> None:
    graph = graph_in("EPSG:4326", highway="service")
    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)
    assert CRS.from_user_input(gdf.crs) == CRS.from_epsg(4326)
    assert list(gdf.geometry.iloc[0].coords)[0] == pytest.approx((LON_A, LAT_A))


def test_wrong_crs_label_would_be_detected_by_coordinates() -> None:
    """Guard: relabelling metres as EPSG:4326 must produce a visibly different result."""
    graph = graph_in(UTM_21S)
    relabelled = graph.copy()
    relabelled.graph["crs"] = "EPSG:4326"
    gdf = osmnx_to_roads.graph_to_roads_geodataframe(relabelled)
    assert abs(list(gdf.geometry.iloc[0].coords)[0][0]) > 1000  # would be ~-58.5 if transformed


def test_edge_without_geometry_uses_node_line_without_mutating_graph(no_domain_cache) -> None:
    graph = graph_in(UTM_21S, geometry=False, highway="track")
    before = snapshot(graph)

    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)

    coords = list(gdf.geometry.iloc[0].coords)
    assert len(coords) == 2
    assert coords[0] == pytest.approx((LON_A, LAT_A), abs=1e-6)
    assert coords[1] == pytest.approx((LON_B, LAT_B), abs=1e-6)
    assert "geometry" not in graph.edges[1, 2, 3]
    assert snapshot(graph) == before
    assert len(build_map(gdf).roads) == 1


def test_edge_without_geometry_and_without_node_coordinates_fails_loudly() -> None:
    graph = graph_in(UTM_21S, geometry=False)
    del graph.nodes[2]["x"]
    with pytest.raises(ValueError, match="no usable geometry"):
        osmnx_to_roads.graph_to_roads_geodataframe(graph)


def test_multipart_geometry_is_preserved_and_split_into_domain_roads(no_domain_cache) -> None:
    graph = graph_in(UTM_21S, geometry=False, highway="primary")
    to_crs = Transformer.from_crs("EPSG:4326", UTM_21S, always_xy=True)
    p = [to_crs.transform(LON_A + i * 0.001, LAT_A) for i in range(4)]
    graph.edges[1, 2, 3]["geometry"] = MultiLineString([[p[0], p[1]], [p[2], p[3]]])

    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)

    assert gdf.geometry.iloc[0].geom_type == "MultiLineString"
    assert len(gdf.geometry.iloc[0].geoms) == 2
    roads = build_map(gdf).roads
    assert len(roads) == 2
    assert {r.id.rsplit(":part:", 1)[-1] for r in roads} == {"0", "1"}
    assert all(r.metadata["osm_attributes"]["highway"] == "primary" for r in roads)


def test_optional_null_attributes_do_not_drop_or_corrupt_edges(no_domain_cache) -> None:
    graph = graph_in(UTM_21S, highway="residential", name=None, bridge=None)
    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)
    assert len(gdf) == 1
    assert gdf.iloc[0]["highway"] == "residential"
    assert gdf.iloc[0]["name"] is None or gdf.iloc[0]["name"] != gdf.iloc[0]["name"]  # None or NaN
    road = build_map(gdf).roads[0]
    assert road.surface == "residential"


def test_graph_without_edges_yields_empty_epsg4326_frame() -> None:
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = UTM_21S
    graph.add_node(1, x=1.0, y=2.0)
    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph)
    assert len(gdf) == 0
    assert CRS.from_user_input(gdf.crs) == CRS.from_epsg(4326)


@pytest.mark.parametrize("crs_value", [None, "not-a-crs"])
def test_missing_or_invalid_graph_crs_raises_instead_of_returning_empty(crs_value) -> None:
    graph = graph_in(UTM_21S)
    if crs_value is None:
        graph.graph.pop("crs")
    else:
        graph.graph["crs"] = crs_value
    with pytest.raises(Exception):
        osmnx_to_roads.graph_to_roads_geodataframe(graph)


def test_projection_failure_in_adapter_is_wrapped_not_swallowed(monkeypatch) -> None:
    import geopandas as gpd

    def boom(self, *_args, **_kwargs):
        raise RuntimeError("PROJ failure")

    monkeypatch.setattr(gpd.GeoDataFrame, "to_crs", boom)
    with pytest.raises(ValueError, match="Could not transform street geometries") as info:
        osmnx_to_roads.graph_to_roads_geodataframe(graph_in(UTM_21S))
    assert isinstance(info.value.__cause__, RuntimeError)


def test_mapdata_rejects_non_epsg4326_roads(no_domain_cache) -> None:
    gdf = osmnx_to_roads.graph_to_roads_geodataframe(graph_in(UTM_21S)).to_crs("EPSG:3857")
    with pytest.raises(ValueError, match="EPSG:4326"):
        build_map(gdf)


def _acquire(monkeypatch, factory):
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: MemoryCache())
    monkeypatch.setattr(osm_data_handler, "map_geometries", {})
    monkeypatch.setattr(osm_data_handler, "networks", {"roads": None})
    calls: list[Any] = []

    def fake(*args, **kwargs):
        calls.append((args, kwargs))
        return factory()

    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", fake)
    return osm_data_handler.download_data_from_bbox(BBOX), calls


@pytest.mark.parametrize("source_crs", ["EPSG:4326", UTM_21S])
def test_acquisition_transforms_provider_graph_to_local_crs_and_round_trips(monkeypatch, no_domain_cache, source_crs) -> None:
    provider_graph = graph_in(source_crs, highway="residential", name="Main Street")
    provider_before = snapshot(provider_graph)
    bundle, calls = _acquire(monkeypatch, lambda: provider_graph)
    result = bundle["roads"]

    assert len(calls) == 1
    assert result.status == "available"
    assert result.graph is not provider_graph  # transformed copy, provider graph untouched
    assert snapshot(provider_graph) == provider_before

    origin_lon = (BBOX[0] + BBOX[2]) / 2
    origin_lat = (BBOX[1] + BBOX[3]) / 2
    local = local_crs_from_lonlat(origin_lon, origin_lat)
    assert CRS.from_user_input(result.graph.graph["crs"]) == local
    assert CRS.from_user_input(result.graph_crs) == local
    expected = Transformer.from_crs("EPSG:4326", local, always_xy=True).transform(LON_A, LAT_A)
    assert (result.graph.nodes[1]["x"], result.graph.nodes[1]["y"]) == pytest.approx(expected, abs=1e-3)
    assert abs(result.graph.nodes[1]["x"]) < 10_000  # local metres, not degrees
    assert result.graph.edges[1, 2, 3]["name"] == "Main Street"

    canonical_before = snapshot(result.graph)
    gdf = osmnx_to_roads.graph_to_roads_geodataframe(result.graph)
    assert snapshot(result.graph) == canonical_before
    assert list(gdf.geometry.iloc[0].coords)[0] == pytest.approx((LON_A, LAT_A), abs=1e-6)
    assert build_map(gdf).coordinate_system == "EPSG:4326"


def test_valid_empty_provider_graph_is_empty_not_failed(monkeypatch) -> None:
    def empty():
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:4326"
        graph.add_node(1, x=LON_A, y=LAT_A)
        return graph

    bundle, _ = _acquire(monkeypatch, empty)
    result = bundle["roads"]
    assert result.status == "empty"
    # P3-U016: nodes without edges are preserved, not discarded.
    assert result.graph is not None
    assert result.graph.number_of_edges() == 0
    assert list(result.graph.nodes) == [1]
    assert CRS.from_user_input(result.graph_crs) == CRS.from_user_input(result.graph.graph["crs"])
    assert CRS.from_user_input(result.graph_crs) != CRS.from_user_input("EPSG:4326")


def test_provider_graph_without_nodes_is_completely_empty(monkeypatch) -> None:
    bundle, _ = _acquire(monkeypatch, nx.MultiDiGraph)
    assert bundle["roads"].status == "empty"
    assert bundle["roads"].graph is None
    assert bundle["roads"].graph_crs is None


def test_nodes_only_graph_without_crs_is_failed_not_empty(monkeypatch) -> None:
    def no_crs():
        graph = nx.MultiDiGraph()
        graph.add_node(1, x=LON_A, y=LAT_A)
        return graph

    bundle, _ = _acquire(monkeypatch, no_crs)
    assert bundle["roads"].status == "failed"
    assert bundle["roads"].graph is None


def test_street_result_contract_for_empty_with_graph() -> None:
    nodes_only = nx.MultiDiGraph(crs="EPSG:32721")
    nodes_only.add_node(1, x=1.0, y=2.0, street_count=0)
    ok = StreetNetworkResult(status="empty", graph=nodes_only, graph_crs="EPSG:32721")
    assert ok.graph is nodes_only

    no_crs_graph = nx.MultiDiGraph()
    no_crs_graph.add_node(1)
    with pytest.raises(ValueError, match="explicit graph CRS"):
        StreetNetworkResult(status="empty", graph=no_crs_graph, graph_crs=None)
    with pytest.raises(ValueError, match="does not match"):
        StreetNetworkResult(status="empty", graph=nodes_only, graph_crs="EPSG:4326")
    with pytest.raises(ValueError, match="cannot carry a graph with edges"):
        edged = graph_in("EPSG:32721")
        StreetNetworkResult(status="empty", graph=edged, graph_crs="EPSG:32721")
    with pytest.raises(ValueError, match="graph=None"):
        StreetNetworkResult(status="empty", graph=nx.MultiDiGraph(crs="EPSG:32721"), graph_crs="EPSG:32721")
    with pytest.raises(ValueError, match="requires a graph with edges"):
        StreetNetworkResult(status="available", graph=nodes_only, graph_crs="EPSG:32721")
    for status in ("not_requested", "missing"):
        with pytest.raises(ValueError, match="cannot carry"):
            StreetNetworkResult(status=status, graph=nodes_only, graph_crs="EPSG:32721")
    with pytest.raises(ValueError, match="cannot carry"):
        StreetNetworkResult(status="failed", graph=nodes_only, graph_crs="EPSG:32721", diagnostic="x")


def test_nodes_only_empty_result_round_trips_through_cache_and_skips_roads(monkeypatch) -> None:
    cache = MemoryCache()
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: cache)
    monkeypatch.setattr(osm_data_handler, "map_geometries", {})
    monkeypatch.setattr(osm_data_handler, "networks", {"roads": None})
    calls = []

    def provider(*_a, **_k):
        calls.append(True)
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:4326"
        graph.add_node(1, x=LON_A, y=LAT_A, street_count=0)
        return graph

    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", provider)
    bbox = (-58.53, -34.77, -58.49, -34.73)
    first = osm_data_handler.download_data_from_bbox(bbox)["roads"]
    second = osm_data_handler.download_data_from_bbox(bbox)["roads"]
    assert len(calls) == 1
    assert second.status == "empty" and second.source == "cache"
    assert list(second.graph.nodes(data=True)) == list(first.graph.nodes(data=True))
    assert second.graph_crs == first.graph_crs
    assert osm_data_handler._OSM_BBOX_ALGORITHM_VERSION == "5"


def test_provider_graph_without_crs_is_failed_not_empty(monkeypatch) -> None:
    def no_crs():
        graph = graph_in("EPSG:4326")
        graph.graph.pop("crs")
        return graph

    bundle, _ = _acquire(monkeypatch, no_crs)
    assert bundle["roads"].status == "failed"
    assert bundle["roads"].diagnostic


def test_provider_graph_with_invalid_crs_is_failed_not_empty(monkeypatch) -> None:
    def bad_crs():
        graph = graph_in("EPSG:4326")
        graph.graph["crs"] = "not-a-crs"
        return graph

    bundle, _ = _acquire(monkeypatch, bad_crs)
    assert bundle["roads"].status == "failed"
    assert bundle["roads"].diagnostic


def test_transform_failure_during_acquisition_is_failed_not_empty(monkeypatch) -> None:
    def failing_transform(*_args, **_kwargs):
        raise RuntimeError("PROJ transform failure")

    monkeypatch.setattr(osm_data_handler, "transform_graph_to_ror", failing_transform)
    bundle, _ = _acquire(monkeypatch, lambda: graph_in("EPSG:4326"))
    assert bundle["roads"].status == "failed"
    assert "RuntimeError" in bundle["roads"].diagnostic
    assert bundle["roads"].graph is None


def test_transform_graph_rejects_node_without_coordinates_and_non_finite_output() -> None:
    graph = graph_in("EPSG:4326")
    del graph.nodes[1]["y"]
    with pytest.raises(ValueError, match="x and y"):
        transform_graph(graph, UTM_21S)

    far = graph_in("EPSG:4326")
    far.nodes[1]["x"] = float("inf")
    with pytest.raises(Exception):
        transform_graph(far, UTM_21S)


# ----------------------------------------------------------------- Task B


@pytest.fixture
def cli_session(monkeypatch, tmp_path):
    """Isolate CLI global state and all external access for CLI integration tests."""
    for name in ("OSM2TERRN_PLACE_NAME", "OSM2TERRN_ORIGIN_LON", "OSM2TERRN_ORIGIN_LAT"):
        monkeypatch.setenv(name, "")
    monkeypatch.setattr(commands.current_map, "data", {})
    monkeypatch.setattr(commands.current_map, "elevation_data", {})
    monkeypatch.setattr(commands.current_map, "place", "unset")
    monkeypatch.setattr(commands.current_map, "origin_lon", 0.0)
    monkeypatch.setattr(commands.current_map, "origin_lat", 0.0)
    monkeypatch.setattr(commands.current_map, "terrain_world_size", None)
    monkeypatch.setattr(commands, "clear", lambda: None)
    monkeypatch.setattr(commands, "download_menu", lambda: ("Fixture City", BBOX))
    monkeypatch.setattr(commands, "heightmapper", lambda _bounds: ([[0.0, 1.0], [1.0, 2.0]], 2.0, 0.0))
    monkeypatch.setattr(osm_data_handler, "get_cache_manager", lambda: MemoryCache())
    monkeypatch.setattr(osm_data_handler, "map_geometries", {})
    monkeypatch.setattr(osm_data_handler, "networks", {"roads": None})
    monkeypatch.setattr(osmnx_to_roads, "get_cache_manager", lambda: NoCache())
    monkeypatch.setattr(osmnx_to_map, "get_cache_manager", lambda: NoCache())
    monkeypatch.setattr(orchestrator, "_PROJECT_CONFIG", _config(include_roads=True))
    monkeypatch.setattr(orchestrator, "_get_output_dir", lambda: str(tmp_path))
    monkeypatch.setattr(
        orchestrator,
        "_export_heightmap_textures",
        lambda **_kwargs: (
            "h.png",
            "g.png",
            {
                "min_elevation": 0.0,
                "max_elevation": 1.0,
                "elevation_range": 1.0,
                "elevation_status": "available",
            },
        ),
    )
    for name in ("export_paged_otc", "export_global_otc", "export_terrn2_entrypoint"):
        monkeypatch.setattr(orchestrator, name, lambda *_a, **_k: None)

    seen: dict[str, Any] = {"maps": [], "road_builds": [], "reloads": 0}
    monkeypatch.setattr(orchestrator, "_write_domain_objects_manifest", lambda domain_map, _path: seen["maps"].append(domain_map))

    def fake_build_roads(**kwargs):
        seen["road_builds"].append(kwargs)
        path = Path(kwargs["output_dir"]) / "roads.tobj"
        path.write_text("// synthetic roads\n", encoding="utf-8")
        return str(path)

    monkeypatch.setattr(orchestrator, "build_roads_from_graph", fake_build_roads)

    def no_reload(*_args, **_kwargs):
        seen["reloads"] += 1
        raise AssertionError("unexpected place-based graph reload")

    monkeypatch.setattr("osm2terrn.data.osm_loader.load_graph", no_reload)
    monkeypatch.setattr("osm2terrn.processing.network.road_network_export.load_graph", no_reload, raising=False)
    return seen


def _config(*, include_roads: bool) -> ProjectConfig:
    config = ProjectConfig(export=ProjectConfig().export)
    config.export.include_roads = include_roads
    config.export.include_buildings = False
    return config


def _provider(monkeypatch, factory) -> list[Any]:
    calls: list[Any] = []

    def fake(*args, **kwargs):
        calls.append(args)
        return factory()

    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", fake)
    return calls


def test_cli_download_then_export_passes_same_canonical_graph_to_consumers(monkeypatch, cli_session) -> None:
    calls = _provider(monkeypatch, lambda: graph_in("EPSG:4326", highway="residential", name="Main Street"))
    exported: list[dict] = []
    real_export = orchestrator.export_terrain_assets
    monkeypatch.setattr(
        commands,
        "export_terrain_assets",
        lambda **kwargs: exported.append(kwargs) or real_export(**kwargs),
    )

    commands.dlcity()
    bundled = commands.current_map.data["roads"]
    assert isinstance(bundled, StreetNetworkResult) and bundled.status == "available"
    canonical = bundled.graph
    before = snapshot(canonical)

    commands.export()

    assert len(calls) == 1  # single provider acquisition for the whole flow
    assert cli_session["reloads"] == 0
    assert len(exported) == 1
    assert exported[0]["road_network"] is bundled
    assert exported[0]["road_network"].graph is canonical
    assert len(cli_session["road_builds"]) == 1
    assert cli_session["road_builds"][0]["graph"] is canonical
    assert snapshot(canonical) == before

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "available"
    assert metadata["road_mapdata_status"] == "available"
    assert metadata["road_export_status"] == "exported"
    assert metadata["roads_exported"] is True
    assert metadata["road_count"] == 1
    assert exported[0]["acquisition_results"] == commands.current_map.data["acquisition_results"]


def test_cli_preserves_initial_world_size_through_export(monkeypatch, cli_session) -> None:
    bbox = (-122.4130, 37.8010, -122.4010, 37.8100)
    monkeypatch.setattr(commands, "download_menu", lambda: ("Telegraph Hill", bbox))
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    exported_sizes: list[dict[str, Any]] = []
    monkeypatch.setattr(
        orchestrator,
        "export_global_otc",
        lambda **kwargs: exported_sizes.append(kwargs),
    )

    commands.dlcity()

    assert commands.current_map.terrain_world_size == 2048

    commands.export()

    assert len(exported_sizes) == 1
    assert exported_sizes[0]["world_size_x"] == 2048
    assert exported_sizes[0]["world_size_z"] == 2048


def test_road_export_uses_configured_directory_from_a_different_working_directory(
    monkeypatch, cli_session, tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))

    commands.dlcity()
    commands.export()

    road_call = cli_session["road_builds"][0]
    road_path = Path(road_call["output_dir"]) / "roads.tobj"
    assert road_call["output_dir"] == str(tmp_path)
    assert road_path.is_file()
    assert not (work_dir / "roads.tobj").exists()


def test_cli_acquisition_failure_is_visible_and_does_not_reacquire_or_export_roads(monkeypatch, cli_session) -> None:
    def failing():
        raise RuntimeError("synthetic provider outage")

    calls = _provider(monkeypatch, failing)
    exported: list[dict] = []
    real_export = orchestrator.export_terrain_assets
    monkeypatch.setattr(
        commands,
        "export_terrain_assets",
        lambda **kwargs: exported.append(kwargs) or real_export(**kwargs),
    )

    commands.dlcity()
    result = commands.current_map.data["roads"]
    assert result.status == "failed" and "RuntimeError" in result.diagnostic

    commands.export()

    assert len(calls) == 1
    assert cli_session["reloads"] == 0
    assert exported[0]["road_network"] is result
    assert cli_session["road_builds"] == []
    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "failed"
    assert metadata["road_mapdata_status"] == "failed"
    assert metadata["road_export_status"] == "skipped"
    assert metadata["roads_exported"] is False
    assert metadata["road_count"] == 0
    assert "RuntimeError" in metadata["road_acquisition_diagnostic"]


def test_cli_empty_street_result_is_reported_as_empty_not_failed(monkeypatch, cli_session) -> None:
    def empty():
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:4326"
        graph.add_node(1, x=LON_A, y=LAT_A)
        return graph

    _provider(monkeypatch, empty)
    commands.dlcity()
    kept = commands.current_map.data["roads"]
    assert kept.status == "empty" and kept.graph is not None and list(kept.graph.nodes) == [1]
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "empty"
    assert metadata["road_mapdata_status"] == "empty"
    assert metadata["road_export_status"] == "skipped"
    assert metadata["roads_exported"] is False
    assert cli_session["road_builds"] == []


def test_cli_reports_requested_but_unimplemented_building_export_as_partial(
    monkeypatch, cli_session
) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    orchestrator._PROJECT_CONFIG.export.include_buildings = True
    messages = _capture_cli(monkeypatch)

    commands.dlcity()
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["building_export_status"] == "not_implemented"
    assert any("Partial export" in message for message in messages)
    assert any("building export is not implemented" in message for message in messages)
    assert not any("Export complete" in message for message in messages)


def test_cli_reports_optional_acquisition_failure_without_hiding_it(
    monkeypatch, cli_session
) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.current_map.data["acquisition_results"]["parks"] = LayerAcquisitionResult(
        status="failed",
        failure_category="temporary",
        failure_stage="acquisition",
        diagnostic="ResponseStatusCodeError (HTTP 502)",
    )

    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["layer_acquisition_results"]["parks"]["status"] == "failed"
    assert any("Export complete with acquisition warnings" in message for message in messages)
    assert any("parks: ResponseStatusCodeError (HTTP 502)" in message for message in messages)
    assert not any("Partial export" in message for message in messages)


def test_elevation_fallback_is_reported_as_partial_export(monkeypatch, cli_session) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    monkeypatch.setattr(
        orchestrator,
        "_export_heightmap_textures",
        lambda **_kwargs: (
            "h.png",
            "g.png",
            {
                "min_elevation": 0.0,
                "max_elevation": 0.0,
                "elevation_range": 0.0,
                "elevation_status": "failed",
            },
        ),
    )
    messages = _capture_cli(monkeypatch)

    commands.dlcity()
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["elevation_status"] == "failed"
    assert any("Partial export" in message for message in messages)
    assert any("flat fallback heightmap" in message for message in messages)
    assert not any("Export complete" in message for message in messages)


def test_cli_export_with_include_roads_false_skips_roads_but_keeps_other_stages(monkeypatch, cli_session) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    monkeypatch.setattr(orchestrator, "_PROJECT_CONFIG", _config(include_roads=False))
    stages: list[str] = []
    for name in ("export_paged_otc", "export_global_otc", "export_terrn2_entrypoint"):
        monkeypatch.setattr(orchestrator, name, lambda *_a, _name=name, **_k: stages.append(_name))
    converted: list[Any] = []
    monkeypatch.setattr(
        orchestrator,
        "graph_to_roads_geodataframe",
        lambda *_a, **_k: converted.append(True) or pytest.fail("conversion must be skipped"),
    )

    commands.dlcity()
    commands.export()

    assert converted == []
    assert cli_session["road_builds"] == []
    assert stages == ["export_paged_otc", "export_global_otc", "export_terrn2_entrypoint"]
    metadata = cli_session["maps"][0].metadata
    assert metadata["road_export_status"] == "disabled"
    assert metadata["road_mapdata_status"] == "disabled"


def test_cli_mapdata_conversion_failure_fails_roads_globally_but_keeps_terrain_stages(monkeypatch, cli_session, caplog) -> None:
    """P3-U015 policy: conversion failure is not an acquisition failure and blocks the .tobj export."""
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    cli_messages: list[str] = []
    monkeypatch.setattr(
        commands.console,
        "print",
        lambda *args, **_kwargs: cli_messages.append(" ".join(str(arg) for arg in args)),
    )

    def broken(*_args, **_kwargs):
        raise ValueError("synthetic conversion failure")

    monkeypatch.setattr(orchestrator, "graph_to_roads_geodataframe", broken)
    stages: list[str] = []
    for name in ("export_paged_otc", "export_global_otc", "export_terrn2_entrypoint"):
        monkeypatch.setattr(orchestrator, name, lambda *_a, _name=name, **_k: stages.append(_name))

    commands.dlcity()
    result = commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "available"
    assert metadata["road_mapdata_status"] == "failed"
    assert "ValueError" in metadata["road_mapdata_diagnostic"]
    assert metadata["road_processing_status"] == "failed"
    assert metadata["road_export_status"] == "failed"
    assert metadata["roads_exported"] is False
    assert metadata["road_count"] == 0
    assert cli_session["road_builds"] == []
    assert stages == ["export_paged_otc", "export_global_otc", "export_terrn2_entrypoint"]
    assert result is None  # export() has no return contract; the outcome is reported via messages

    assert "Could not adapt street graph to MapData" in caplog.text
    assert "street graph to MapData conversion failed" in caplog.text
    assert "Partial export" in caplog.text
    assert any("Partial export" in message and "roads were NOT exported" in message for message in cli_messages)
    assert not any("Export complete" in message for message in cli_messages)


def _capture_cli(monkeypatch) -> list[str]:
    messages: list[str] = []
    monkeypatch.setattr(commands.console, "print", lambda *args, **_k: messages.append(" ".join(str(a) for a in args)))
    return messages


def test_cli_full_export_reports_complete_success(monkeypatch, cli_session, caplog) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_export_status"] == "exported" and metadata["roads_exported"] is True
    assert any("Export complete" in m for m in messages)
    assert not any("Partial export" in m for m in messages)
    assert "Partial export" not in caplog.text
    assert not any("roads_outcome" in m for m in messages)


def test_cli_valid_empty_graph_is_not_a_partial_export(monkeypatch, cli_session, caplog) -> None:
    def nodes_only():
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:4326"
        graph.add_node(1, x=LON_A, y=LAT_A)
        return graph

    _provider(monkeypatch, nodes_only)
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "empty"
    assert metadata["road_export_status"] == "skipped"
    assert any("Export complete" in m for m in messages)
    assert not any("Partial export" in m for m in messages)
    assert "Partial export" not in caplog.text


def test_cli_acquisition_failure_is_reported_as_partial_export(monkeypatch, cli_session) -> None:
    def failing():
        raise RuntimeError("synthetic provider outage")

    _provider(monkeypatch, failing)
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "failed"
    assert metadata["road_export_status"] == "skipped"  # statuses stay separate
    assert any("Partial export" in m for m in messages)
    assert not any("Export complete" in m for m in messages)


def test_cli_include_roads_false_is_complete_export(monkeypatch, cli_session) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    monkeypatch.setattr(orchestrator, "_PROJECT_CONFIG", _config(include_roads=False))
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.export()

    assert any("Export complete" in m for m in messages)
    assert not any("Partial export" in m for m in messages)


def test_cli_mandatory_terrain_stage_failure_is_not_reported_as_success(monkeypatch, cli_session, caplog) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))

    def failing_otc(*_a, **_k):
        raise RuntimeError("synthetic otc failure")

    monkeypatch.setattr(orchestrator, "export_global_otc", failing_otc)
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.export()

    assert any("Error during export" in m and "synthetic otc failure" in m for m in messages)
    assert not any("Export complete" in m or "Partial export" in m for m in messages)
    assert "Partial export" not in caplog.text


def test_export_terrain_assets_reports_road_outcome_without_changing_other_keys(monkeypatch, cli_session) -> None:
    graph = graph_in("EPSG:4326")
    result = StreetNetworkResult(status="available", graph=graph, graph_crs="EPSG:4326")
    paths = orchestrator.export_terrain_assets(
        "Fixture City", BoundingBox(*BBOX, crs="EPSG:4326"), road_network=result
    )
    assert paths["roads_outcome"] == "exported"
    assert paths["roads_tobj"].endswith("roads.tobj")
    assert {"terrn2", "global_otc", "page_otc", "heightmap", "groundmap", "tobj"} <= set(paths)


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ({"road_export_status": "disabled"}, "disabled"),
        ({"road_export_status": "exported", "road_acquisition_status": "available"}, "exported"),
        ({"road_export_status": "skipped", "road_acquisition_status": "empty"}, "skipped"),
        ({"road_export_status": "skipped", "road_acquisition_status": "failed"}, "failed"),
        ({"road_export_status": "failed", "road_acquisition_status": "available"}, "failed"),
        ({"road_export_status": "skipped", "road_acquisition_status": "missing"}, "failed"),
        ({"road_export_status": "skipped", "road_acquisition_status": "not_requested"}, "not_requested"),
    ],
)
def test_roads_outcome_keeps_separate_statuses_but_flags_lost_roads(metadata, expected) -> None:
    assert orchestrator._roads_outcome(metadata) == expected


def test_invalid_street_result_is_acquisition_failure_distinct_from_conversion_failure(monkeypatch, cli_session) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    commands.dlcity()
    commands.current_map.data["roads"] = object()
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "failed"
    assert metadata["road_mapdata_status"] == "failed"
    assert "TypeError" in metadata["road_mapdata_diagnostic"]
    assert metadata["road_export_status"] == "failed"
    assert cli_session["road_builds"] == []


@pytest.mark.parametrize("lost_value", ["absent", None])
def test_cli_lost_street_result_is_partial_export_not_success(monkeypatch, cli_session, caplog, lost_value) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    if lost_value == "absent":
        del commands.current_map.data["roads"]
    else:
        commands.current_map.data["roads"] = None
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "missing"
    assert metadata["road_mapdata_status"] == "missing"
    assert metadata["road_export_status"] == "skipped"
    assert metadata["roads_exported"] is False
    assert cli_session["road_builds"] == []
    assert any("Partial export" in m for m in messages)
    assert not any("Export complete" in m for m in messages)
    assert "Partial export" in caplog.text


def test_cli_roads_not_requested_by_network_config_is_reported_not_complete(monkeypatch, cli_session, caplog) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    monkeypatch.setattr(osm_data_handler, "networks", {})
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    assert commands.current_map.data["roads"].status == "not_requested"
    commands.export()

    metadata = cli_session["maps"][0].metadata
    assert metadata["road_acquisition_status"] == "not_requested"
    assert metadata["road_export_status"] == "skipped"
    assert cli_session["road_builds"] == []
    assert any("Partial export" in m and "not requested" in m for m in messages)
    assert not any("Export complete" in m for m in messages)
    assert "Partial export" in caplog.text


def test_cli_roads_disabled_with_lost_result_is_still_complete(monkeypatch, cli_session) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    monkeypatch.setattr(orchestrator, "_PROJECT_CONFIG", _config(include_roads=False))
    messages = _capture_cli(monkeypatch)
    commands.dlcity()
    commands.current_map.data["roads"] = None
    commands.export()

    assert cli_session["maps"][0].metadata["road_export_status"] == "disabled"
    assert any("Export complete" in m for m in messages)
    assert not any("Partial export" in m for m in messages)


def test_cli_export_without_downloaded_data_does_not_touch_orchestrator(monkeypatch, cli_session) -> None:
    monkeypatch.setattr(commands, "export_terrain_assets", lambda **_k: pytest.fail("must not export without data"))
    commands.export()
    assert cli_session["road_builds"] == []


def test_cli_cancelled_download_leaves_no_street_state(monkeypatch, cli_session) -> None:
    monkeypatch.setattr(commands, "download_menu", lambda: ("", None))
    monkeypatch.setattr(osm_data_handler.ox, "graph_from_bbox", lambda *_a, **_k: pytest.fail("no acquisition on cancel"))
    commands.dlcity()
    assert commands.current_map.data == {}


def test_cli_export_error_is_reported_not_raised(monkeypatch, cli_session) -> None:
    _provider(monkeypatch, lambda: graph_in("EPSG:4326"))
    commands.dlcity()

    def boom(**_kwargs):
        raise RuntimeError("synthetic export error")

    monkeypatch.setattr(commands, "export_terrain_assets", boom)
    messages: list[str] = []
    monkeypatch.setattr(commands.console, "print", lambda *args, **_k: messages.append(" ".join(str(a) for a in args)))
    commands.export()
    assert any("Error during export" in m and "synthetic export error" in m for m in messages)
