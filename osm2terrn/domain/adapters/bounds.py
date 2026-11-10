from __future__ import annotations

from typing import Any

from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.utils.geometry.crs import determine_is_projected


def to_domain_bounding_box(bounds: Any) -> BoundingBox | None:
    """Convert common bounds-like inputs to a domain BoundingBox."""
    if bounds is None:
        return None

    if isinstance(bounds, BoundingBox):
        return bounds

    if isinstance(bounds, dict):
        try:
            bbox_obj = BoundingBox(bounds)
            crs = bounds.get("crs")
            if isinstance(crs, str) and crs.strip():
                bbox_obj.crs = crs.strip()
                bbox_obj.is_projected = determine_is_projected(bbox_obj.crs)
            return bbox_obj
        except (TypeError, ValueError):
            return None

    if isinstance(bounds, (tuple, list)) and len(bounds) == 4:
        min_x, min_y, max_x, max_y = bounds
        return BoundingBox(float(min_x), float(min_y), float(max_x), float(max_y))

    if hasattr(bounds, "total_bounds"):
        total_bounds = getattr(bounds, "total_bounds")
        if total_bounds is None:
            return None
        min_x, min_y, max_x, max_y = map(float, total_bounds)
        crs_obj = getattr(bounds, "crs", None)
        crs_text = str(crs_obj) if crs_obj is not None else None
        is_projected = determine_is_projected(crs_text) if crs_text else False
        return BoundingBox(min_x, min_y, max_x, max_y, crs=crs_text, is_projected=is_projected)

    if hasattr(bounds, "min_x") and hasattr(bounds, "min_y") and hasattr(bounds, "max_x") and hasattr(bounds, "max_y"):
        bbox_obj = BoundingBox(
            float(getattr(bounds, "min_x")),
            float(getattr(bounds, "min_y")),
            float(getattr(bounds, "max_x")),
            float(getattr(bounds, "max_y")),
        )
        crs = getattr(bounds, "crs", None)
        if crs is not None:
            bbox_obj.crs = str(crs)
            bbox_obj.is_projected = determine_is_projected(bbox_obj.crs)
        return bbox_obj

    if hasattr(bounds, "west") and hasattr(bounds, "south") and hasattr(bounds, "east") and hasattr(bounds, "north"):
        bbox_obj = BoundingBox(
            float(getattr(bounds, "west")),
            float(getattr(bounds, "south")),
            float(getattr(bounds, "east")),
            float(getattr(bounds, "north")),
        )
        crs = getattr(bounds, "crs", None)
        if crs is not None:
            bbox_obj.crs = str(crs)
            bbox_obj.is_projected = determine_is_projected(bbox_obj.crs)
        return bbox_obj

    return None


def require_domain_bounding_box(bounds: Any) -> BoundingBox:
    """Return the domain BoundingBox or raise a ValueError if conversion fails."""
    domain_bbox = to_domain_bounding_box(bounds)
    if domain_bbox is None:
        raise ValueError("Bounds are required and must be convertible to domain BoundingBox")
    return domain_bbox
