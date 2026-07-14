"""Generic SHA-256 digest utilities."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def bytes_sha256(payload: bytes) -> str:
    """Return the hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(payload).hexdigest()


def text_sha256(payload: str, encoding: str = "utf-8") -> str:
    """Return the hex SHA-256 digest of text."""
    return bytes_sha256(payload.encode(encoding))


def stable_object_sha256(payload: Any) -> str:
    """Return a deterministic SHA-256 digest for JSON-serializable objects."""
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text_sha256(normalized)
