"""Storage backend abstractions for cache artifacts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from osm2terrn.cache.metadata import CacheMetadata


class CacheBackend(ABC):
    """Abstract cache backend interface.

    Backends store opaque bytes and metadata. They are intentionally unaware
    of artifact types and serialization details.
    """

    @abstractmethod
    def get(self, namespace: str, key: str) -> tuple[bytes, CacheMetadata] | None:
        """Return cached payload and metadata, or ``None`` if not found."""

    @abstractmethod
    def put(self, namespace: str, key: str, payload: bytes, metadata: CacheMetadata) -> None:
        """Persist a cache payload and associated metadata."""

    @abstractmethod
    def exists(self, namespace: str, key: str) -> bool:
        """Return whether a cache key exists."""

    @abstractmethod
    def remove(self, namespace: str, key: str) -> bool:
        """Remove a cache entry and return ``True`` if it existed."""

    @abstractmethod
    def clear(self, namespace: str | None = None) -> None:
        """Clear all cache entries or only a namespace subtree."""
