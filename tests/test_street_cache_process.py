"""Process-isolated persistence checks for the street-network cache contract."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_process(cache_root: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script, str(cache_root)],
        check=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        text=True,
    )


def test_street_network_result_persists_between_processes(tmp_path: Path) -> None:
    cache_root = tmp_path / "process-cache"
    writer = r"""
import os
import sys
import networkx as nx
from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.data.street_network import StreetNetworkResult

empty = StreetNetworkResult(status="empty", source="query")
nodes = nx.MultiDiGraph()
nodes.graph["crs"] = "EPSG:32721"
nodes.add_node("isolated", x=10.0, y=20.0, street_count=0)
nodes_only = StreetNetworkResult(
    status="empty", graph=nodes, graph_crs="EPSG:32721", source="query"
)
edges = nx.MultiDiGraph()
edges.graph["crs"] = "EPSG:32721"
edges.add_node(1, x=10.0, y=20.0)
edges.add_node(2, x=11.0, y=21.0)
edges.add_edge(1, 2, key=7, highway="residential", name="Cache Road")
available = StreetNetworkResult(
    status="available", graph=edges, graph_crs="EPSG:32721", source="query"
)
manager = CacheManager(FileCacheBackend(sys.argv[1]))
manager.put(
    namespace="street-process-test",
    key="states",
    value=[empty, nodes_only, available],
    serializer=PickleSerializer(),
    metadata=CacheMetadata(artifact_type="street-result-process-test"),
)
print(os.getpid())
"""
    reader = r"""
import json
import os
import sys
from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.data.street_network import StreetNetworkResult

manager = CacheManager(FileCacheBackend(sys.argv[1]))
cached = manager.get(
    namespace="street-process-test",
    key="states",
    serializer=PickleSerializer(),
)
assert cached is not None
results, metadata = cached
assert all(isinstance(item, StreetNetworkResult) for item in results)
empty, nodes_only, available = results
for item in results:
    item.validate()
assert empty.status == "empty" and empty.graph is None
assert nodes_only.status == "empty" and list(nodes_only.graph.nodes) == ["isolated"]
assert nodes_only.graph.nodes["isolated"]["street_count"] == 0
assert nodes_only.graph_crs == "EPSG:32721"
assert available.status == "available" and available.graph.number_of_edges() == 1
assert available.graph.edges[1, 2, 7]["name"] == "Cache Road"
print(json.dumps({"pid": os.getpid(), "serializer": metadata.serializer, "states": [r.status for r in results]}))
"""

    written = _run_process(cache_root, writer)
    restored = _run_process(cache_root, reader)

    restored_data = json.loads(restored.stdout)
    assert written.stdout.strip().isdigit()
    assert restored_data["pid"] != int(written.stdout.strip())
    assert restored_data["serializer"] == "pickle"
    assert restored_data["states"] == ["empty", "empty", "available"]


def test_algorithm_version_three_does_not_reuse_version_two_bundle(tmp_path: Path) -> None:
    cache_root = tmp_path / "versioned-cache"
    write_legacy_entry = r"""
import sys
import networkx as nx
from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.data import osm_data_handler as handler

manager = CacheManager(FileCacheBackend(sys.argv[1]))
handler.get_cache_manager = lambda: manager
handler.map_geometries = {}
handler.networks = {"roads": None}
handler._OSM_BBOX_ALGORITHM_VERSION = "2"
handler.ox.graph_from_bbox = lambda *_args, **_kwargs: nx.MultiDiGraph()
result = handler.download_data_from_bbox((-58.53, -34.77, -58.49, -34.73))
assert result["roads"].status == "empty"
assert result["roads"].graph is None
print("legacy-v2-entry-written")
"""
    load_with_version_three = r"""
import json
import sys
import networkx as nx
from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.data import osm_data_handler as handler

manager = CacheManager(FileCacheBackend(sys.argv[1]))
handler.get_cache_manager = lambda: manager
handler.map_geometries = {}
handler.networks = {"roads": None}
provider_calls = []
def provider(*_args, **_kwargs):
    provider_calls.append(True)
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = "EPSG:4326"
    graph.add_node("preserved", x=-58.52, y=-34.76, street_count=0)
    return graph
def transform(graph, *_args):
    return graph.copy()
handler.ox.graph_from_bbox = provider
handler.transform_graph_to_ror = transform
assert handler._OSM_BBOX_ALGORITHM_VERSION == "5"
result = handler.download_data_from_bbox((-58.53, -34.77, -58.49, -34.73))
streets = result["roads"]
assert len(provider_calls) == 1
assert streets.status == "empty" and streets.source == "query"
assert list(streets.graph.nodes) == ["preserved"]
print(json.dumps({"provider_calls": len(provider_calls), "source": streets.source, "node": list(streets.graph.nodes)}))
"""

    written = _run_process(cache_root, write_legacy_entry)
    loaded = _run_process(cache_root, load_with_version_three)

    assert written.stdout.strip() == "legacy-v2-entry-written"
    assert loaded.stdout.strip() == '{"provider_calls": 1, "source": "query", "node": ["preserved"]}'
