"""Cache path and policy helpers backed by ProgramConfig."""

from __future__ import annotations

from pathlib import Path

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.config.settings import get_program_config

_CACHE_MANAGER: CacheManager | None = None
_CACHE_SIGNATURE: tuple[bool, Path] | None = None


def cache_enabled() -> bool:
    """Return whether caching is enabled."""

    return bool(get_program_config().cache.enabled)


def cache_root() -> Path:
    """Return configured cache root directory."""

    return get_program_config().paths.cache_dir


def ensure_cache_dir() -> Path:
    """Ensure and return cache root directory."""

    root = cache_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def max_cache_size_mb() -> int:
    """Return configured cache size budget in megabytes."""

    return int(get_program_config().cache.max_size_mb)


def get_cache_manager() -> CacheManager:
    """Return a configured cache manager singleton.

    The manager is recreated only when cache settings change.
    """

    global _CACHE_MANAGER, _CACHE_SIGNATURE

    enabled = cache_enabled()
    root = ensure_cache_dir()
    signature = (enabled, root)
    if _CACHE_MANAGER is None or _CACHE_SIGNATURE != signature:
        _CACHE_MANAGER = CacheManager(backend=FileCacheBackend(root), enabled=enabled)
        _CACHE_SIGNATURE = signature
    return _CACHE_MANAGER


def invalidate_cache_namespace(namespace: str) -> None:
    """Invalidate one cache namespace subtree."""

    get_cache_manager().clear(namespace)


def invalidate_cache_provider(provider: str) -> None:
    """Invalidate all cache entries for one provider namespace."""

    invalidate_cache_namespace(f"providers/{provider}")


def invalidate_cache_stage(stage: str) -> None:
    """Invalidate all cache entries for one processing stage namespace."""

    invalidate_cache_namespace(f"processing/{stage}")


def clear_all_cache() -> None:
    """Clear complete cache storage."""

    get_cache_manager().clear()
