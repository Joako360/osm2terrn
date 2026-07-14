"""Backward-compatible re-exports for point value objects.

This module is kept for import compatibility. Prefer importing from
`osm2terrn.domain.value_objects`.
"""

from osm2terrn.domain.value_objects import Point2D, Point3D

__all__ = ["Point2D", "Point3D"]