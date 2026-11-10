"""Serializer contracts and default implementations for cache artifacts."""

from __future__ import annotations

import json
import pickle
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")


class ArtifactSerializer(Protocol[T]):
    """Serialize and deserialize artifact values to opaque bytes."""

    name: str
    content_type: str

    def dumps(self, value: T) -> bytes:
        """Serialize a value into bytes."""

    def loads(self, payload: bytes) -> T:
        """Deserialize bytes into the original value."""


class BytesSerializer:
    """Pass-through serializer for pre-encoded byte payloads."""

    name = "bytes"
    content_type = "application/octet-stream"

    def dumps(self, value: bytes) -> bytes:
        return value

    def loads(self, payload: bytes) -> bytes:
        return payload


class PickleSerializer(Generic[T]):
    """Generic serializer based on Python pickle."""

    name = "pickle"
    content_type = "application/python-pickle"

    def dumps(self, value: T) -> bytes:
        return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

    def loads(self, payload: bytes) -> T:
        return pickle.loads(payload)


class JsonSerializer:
    """Serializer for JSON-compatible artifacts."""

    name = "json"
    content_type = "application/json"

    def dumps(self, value: Any) -> bytes:
        text = json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        return text.encode("utf-8")

    def loads(self, payload: bytes) -> Any:
        return json.loads(payload.decode("utf-8"))
