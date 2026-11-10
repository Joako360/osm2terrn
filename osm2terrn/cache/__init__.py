"""Generic cache infrastructure for reusable pipeline artifacts."""

from osm2terrn.cache.backend import CacheBackend
from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.keys import build_cache_key
from osm2terrn.cache.manager import CacheManager
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import ArtifactSerializer, BytesSerializer, JsonSerializer, PickleSerializer

__all__ = [
    "ArtifactSerializer",
    "BytesSerializer",
    "CacheBackend",
    "CacheManager",
    "CacheMetadata",
    "FileCacheBackend",
    "JsonSerializer",
    "PickleSerializer",
    "build_cache_key",
]
