"""Cache manager coordinating keys, serializers, and backends."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Mapping, TypeVar

from osm2terrn.cache.backend import CacheBackend
from osm2terrn.cache.keys import build_cache_key
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import ArtifactSerializer

T = TypeVar("T")


class CacheManager:
    """High-level cache API independent from concrete storage backends."""

    def __init__(self, backend: CacheBackend, enabled: bool = True) -> None:
        self._backend = backend
        self._enabled = bool(enabled)

    @property
    def enabled(self) -> bool:
        """Return whether this manager should perform cache operations."""

        return self._enabled

    def build_key(
        self,
        key_inputs: Mapping[str, Any],
        *,
        provider: str | None = None,
        algorithm_version: str | None = None,
        format_version: str | None = None,
        artifact_type: str | None = None,
    ) -> str:
        """Build a stable key for a cache artifact."""

        return build_cache_key(
            key_inputs,
            provider=provider,
            algorithm_version=algorithm_version,
            format_version=format_version,
            artifact_type=artifact_type,
        )

    def get(
        self,
        *,
        namespace: str,
        key: str,
        serializer: ArtifactSerializer[T],
    ) -> tuple[T, CacheMetadata] | None:
        """Get and deserialize an artifact from cache."""

        if not self._enabled:
            return None
        entry = self._backend.get(namespace, key)
        if entry is None:
            return None
        payload, metadata = entry
        return serializer.loads(payload), metadata

    def put(
        self,
        *,
        namespace: str,
        key: str,
        value: T,
        serializer: ArtifactSerializer[T],
        metadata: CacheMetadata | None = None,
    ) -> CacheMetadata:
        """Serialize and store an artifact in cache."""

        payload = serializer.dumps(value)
        base_metadata = metadata or CacheMetadata()
        final_metadata = replace(
            base_metadata,
            size_bytes=len(payload),
            serializer=serializer.name,
            content_type=serializer.content_type,
        )
        if self._enabled:
            self._backend.put(namespace, key, payload, final_metadata)
        return final_metadata

    def get_or_compute(
        self,
        *,
        namespace: str,
        key: str,
        serializer: ArtifactSerializer[T],
        compute: Callable[[], T],
        metadata: CacheMetadata | None = None,
    ) -> tuple[T, bool]:
        """Return cached value or compute/store it.

        Returns ``(value, cache_hit)``.
        """

        cached = self.get(namespace=namespace, key=key, serializer=serializer)
        if cached is not None:
            return cached[0], True
        value = compute()
        self.put(namespace=namespace, key=key, value=value, serializer=serializer, metadata=metadata)
        return value, False

    def exists(self, *, namespace: str, key: str) -> bool:
        """Check if an artifact key exists in cache."""

        if not self._enabled:
            return False
        return self._backend.exists(namespace, key)

    def remove(self, *, namespace: str, key: str) -> bool:
        """Remove one cached artifact."""

        if not self._enabled:
            return False
        return self._backend.remove(namespace, key)

    def clear(self, namespace: str | None = None) -> None:
        """Clear all entries or one namespace."""

        if not self._enabled:
            return
        self._backend.clear(namespace)
