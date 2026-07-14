from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain-layer failures."""


class ValidationError(DomainError):
    """Raised when a domain value object violates its invariants."""
