from __future__ import annotations

import math
from typing import Any

from osm2terrn.config.settings import get_program_config
from osm2terrn.domain.value_objects import BoundingBox

_PROGRAM_CONFIG = get_program_config()


def to_domain_bounding_box(bounds: Any) -> BoundingBox | None:
    """Convert common bounds-like inputs to a domain BoundingBox."""
    if bounds is None:
        return None

    if isinstance(bounds, BoundingBox):
        return bounds

    if isinstance(bounds, (tuple, list)) and len(bounds) == 4:
        min_x, min_y, max_x, max_y = bounds
        return BoundingBox(float(min_x), float(min_y), float(max_x), float(max_y))

    if hasattr(bounds, "total_bounds"):
        total_bounds = getattr(bounds, "total_bounds")
        if total_bounds is None:
            return None
        min_x, min_y, max_x, max_y = map(float, total_bounds)
        return BoundingBox(min_x, min_y, max_x, max_y)

    if hasattr(bounds, "min_x") and hasattr(bounds, "min_y") and hasattr(bounds, "max_x") and hasattr(bounds, "max_y"):
        return BoundingBox(
            float(getattr(bounds, "min_x")),
            float(getattr(bounds, "min_y")),
            float(getattr(bounds, "max_x")),
            float(getattr(bounds, "max_y")),
        )

    return None


def compute_world_params(
    bounds: Any,
    page_size: int = _PROGRAM_CONFIG.terrain_runtime.page_size,
    snap_to_pow2: bool = True,
) -> tuple[int, float]:
    """Compute a square world size from a bounds-like object using domain values only."""
    domain_bounds = to_domain_bounding_box(bounds)
    if domain_bounds is None:
        return int(max(page_size - 1, 1)), 1.0

    width = domain_bounds.width
    height = domain_bounds.height
    side = max(width, height)
    if side <= 0:
        return int(max(page_size - 1, 1)), 1.0

    if snap_to_pow2:
        world_size = 1
        while world_size < side:
            world_size <<= 1
    else:
        world_size = int(math.ceil(side))

    meters_per_pixel = float(world_size) / float(max(page_size - 1, 1))
    return int(world_size), float(meters_per_pixel)
