"""Global cache versioning for coordinated pipeline invalidation."""

from __future__ import annotations


# Bump this value to invalidate cache keys across the whole pipeline.
PIPELINE_CACHE_VERSION = "1"
