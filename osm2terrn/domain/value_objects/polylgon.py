"""Backward-compatible re-export for legacy misspelled polygon module.

This module is kept for import compatibility. Prefer importing from
`osm2terrn.domain.value_objects`.
"""

from osm2terrn.domain.value_objects import Polygon

__all__ = ["Polygon"]