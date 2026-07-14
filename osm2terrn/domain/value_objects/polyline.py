"""Backward-compatible re-export for polyline value object.

This module is kept for import compatibility. Prefer importing from
`osm2terrn.domain.value_objects`.
"""

from osm2terrn.domain.value_objects import Polyline

__all__ = ["Polyline"]