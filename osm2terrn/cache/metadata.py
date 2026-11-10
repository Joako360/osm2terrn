"""Metadata model for cache entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class CacheMetadata:
    """Metadata associated with a cached artifact.

    The schema includes explicit version fields used by cache key generation
    and future invalidation policies.
    """

    created_at: datetime = field(default_factory=_utc_now)
    size_bytes: int = 0
    artifact_type: str | None = None
    provider: str | None = None
    algorithm_version: str | None = None
    format_version: str | None = None
    serializer: str | None = None
    content_type: str | None = None
    version: str = "1"
    expires_at: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, now: datetime | None = None) -> bool:
        """Return whether metadata indicates an expired entry."""

        if self.expires_at is None:
            return False
        ref = now or _utc_now()
        return ref >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to a JSON-safe dictionary."""

        return {
            "created_at": self.created_at.isoformat(),
            "size_bytes": int(self.size_bytes),
            "artifact_type": self.artifact_type,
            "provider": self.provider,
            "algorithm_version": self.algorithm_version,
            "format_version": self.format_version,
            "serializer": self.serializer,
            "content_type": self.content_type,
            "version": self.version,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheMetadata":
        """Create metadata from a dictionary representation."""

        created_at_raw = data.get("created_at")
        expires_at_raw = data.get("expires_at")
        return cls(
            created_at=datetime.fromisoformat(created_at_raw) if created_at_raw else _utc_now(),
            size_bytes=int(data.get("size_bytes", 0)),
            artifact_type=data.get("artifact_type"),
            provider=data.get("provider"),
            algorithm_version=data.get("algorithm_version"),
            format_version=data.get("format_version"),
            serializer=data.get("serializer"),
            content_type=data.get("content_type"),
            version=str(data.get("version", "1")),
            expires_at=datetime.fromisoformat(expires_at_raw) if expires_at_raw else None,
            extra=dict(data.get("extra", {})),
        )
