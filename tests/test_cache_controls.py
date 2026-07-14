from __future__ import annotations

from pathlib import Path

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.keys import build_cache_key
from osm2terrn.cache.manager import CacheManager
from osm2terrn.cache.serializers import JsonSerializer
from osm2terrn.config import cache as cache_config


def test_build_cache_key_changes_when_pipeline_version_changes(monkeypatch) -> None:
    payload = {"a": 1}
    key_v1 = build_cache_key(payload, artifact_type="x")
    monkeypatch.setattr("osm2terrn.cache.keys.PIPELINE_CACHE_VERSION", "2")
    key_v2 = build_cache_key(payload, artifact_type="x")

    assert key_v1 != key_v2


def test_invalidate_cache_namespace_clears_only_target(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(cache_config, "get_cache_manager", lambda: manager)
    serializer = JsonSerializer()

    manager.put(namespace="providers/osm/graph", key="k1", value={"x": 1}, serializer=serializer)
    manager.put(namespace="providers/elevation/raster", key="k2", value={"y": 1}, serializer=serializer)

    cache_config.invalidate_cache_provider("osm")

    assert manager.get(namespace="providers/osm/graph", key="k1", serializer=serializer) is None
    assert manager.get(namespace="providers/elevation/raster", key="k2", serializer=serializer) is not None
