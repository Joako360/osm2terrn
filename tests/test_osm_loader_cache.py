from __future__ import annotations

from pathlib import Path

import networkx as nx

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.data import osm_loader


def test_load_graph_uses_cache_for_identical_inputs(monkeypatch, tmp_path: Path) -> None:
    call_counter = {"count": 0}

    def fake_graph_from_place(place: str, network_type: str, simplify: bool) -> nx.MultiDiGraph:
        call_counter["count"] += 1
        graph = nx.MultiDiGraph()
        graph.add_node(1, x=0.0, y=0.0)
        graph.add_node(2, x=1.0, y=1.0)
        graph.add_edge(1, 2, key=0)
        graph.graph["source"] = place
        return graph

    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(osm_loader, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(osm_loader.ox, "graph_from_place", fake_graph_from_place)

    g1 = osm_loader.load_graph(place="X", network_type="drive", simplify=True)
    g2 = osm_loader.load_graph(place="X", network_type="drive", simplify=True)

    assert call_counter["count"] == 1
    assert isinstance(g1, nx.MultiDiGraph)
    assert isinstance(g2, nx.MultiDiGraph)
    assert g1.graph["source"] == "X"
    assert g2.graph["source"] == "X"
