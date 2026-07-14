from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DomainEntity:
    """Base class for domain entities.

    Attributes:
        id: Stable identifier for the entity.
        metadata: Optional metadata dictionary that can preserve source-specific
            information without coupling the domain to a single provider.
    """

    id: str
    metadata: dict[str, Any] = field(default_factory=dict, kw_only=True)
