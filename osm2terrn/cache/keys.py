"""Stable cache key generation utilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from osm2terrn.cache.version import PIPELINE_CACHE_VERSION


def _canonicalize(value: Any) -> Any:
    """Convert arbitrary values to a JSON-stable representation."""

    if is_dataclass(value):
        return _canonicalize(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, set):
        return [_canonicalize(item) for item in sorted(value, key=repr)]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return repr(value)


def stable_hash(payload: Any) -> str:
    """Return a SHA256 hash for canonical payload data."""

    canonical = _canonicalize(payload)
    encoded = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_cache_key(
    key_inputs: Mapping[str, Any],
    *,
    provider: str | None = None,
    algorithm_version: str | None = None,
    format_version: str | None = None,
    artifact_type: str | None = None,
) -> str:
    """Build a stable cache key from execution inputs and versions."""

    payload = {
        "pipeline_cache_version": PIPELINE_CACHE_VERSION,
        "artifact_type": artifact_type,
        "provider": provider,
        "algorithm_version": algorithm_version,
        "format_version": format_version,
        "inputs": dict(key_inputs),
    }
    return stable_hash(payload)
