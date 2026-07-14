from __future__ import annotations

from pathlib import Path

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.keys import build_cache_key
from osm2terrn.cache.manager import CacheManager
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import JsonSerializer


def test_build_cache_key_is_stable_for_dict_order() -> None:
    key_a = build_cache_key(
        {"b": 2, "a": {"x": [1, 2, 3]}},
        provider="osm",
        algorithm_version="v1",
        format_version="f1",
        artifact_type="roads",
    )
    key_b = build_cache_key(
        {"a": {"x": [1, 2, 3]}, "b": 2},
        provider="osm",
        algorithm_version="v1",
        format_version="f1",
        artifact_type="roads",
    )
    key_c = build_cache_key(
        {"a": {"x": [1, 2, 3]}, "b": 2},
        provider="osm",
        algorithm_version="v2",
        format_version="f1",
        artifact_type="roads",
    )

    assert key_a == key_b
    assert key_a != key_c


def test_cache_manager_roundtrip_with_file_backend(tmp_path: Path) -> None:
    backend = FileCacheBackend(tmp_path / "cache")
    manager = CacheManager(backend=backend, enabled=True)
    serializer = JsonSerializer()
    namespace = "processing/intermediate"
    key = manager.build_key(
        {"input": "roads", "tile": 1},
        provider="osm",
        algorithm_version="v1",
        format_version="f1",
        artifact_type="road_network",
    )
    payload = {"roads": [{"id": 1, "name": "A"}]}

    manager.put(
        namespace=namespace,
        key=key,
        value=payload,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="road_network",
            provider="osm",
            algorithm_version="v1",
            format_version="f1",
            extra={"stage": "process"},
        ),
    )

    cached = manager.get(namespace=namespace, key=key, serializer=serializer)
    assert cached is not None
    value, metadata = cached
    assert value == payload
    assert metadata.artifact_type == "road_network"
    assert metadata.extra["stage"] == "process"
    assert metadata.size_bytes > 0
    assert manager.exists(namespace=namespace, key=key)

    assert manager.remove(namespace=namespace, key=key)
    assert manager.get(namespace=namespace, key=key, serializer=serializer) is None


def test_cache_manager_disabled_does_not_persist(tmp_path: Path) -> None:
    backend = FileCacheBackend(tmp_path / "cache")
    manager = CacheManager(backend=backend, enabled=False)
    serializer = JsonSerializer()
    key = manager.build_key({"a": 1}, artifact_type="artifact")

    manager.put(namespace="x", key=key, value={"a": 1}, serializer=serializer)
    assert manager.get(namespace="x", key=key, serializer=serializer) is None
    assert list((tmp_path / "cache").rglob("*")) == []
