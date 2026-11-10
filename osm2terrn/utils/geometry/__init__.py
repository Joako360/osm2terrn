"""Generic geometry utilities reusable across projects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from osm2terrn.utils.geometry.crs import (
    determine_is_projected,
    local_crs_from_lonlat,
    to_local_coords,
    utm_crs_from_lonlat,
)

if TYPE_CHECKING:
    from osm2terrn.utils.geometry.bounds import (
        _next_power_of_two,
        bbox_size_meters,
        compute_world_params,
        make_square_bounds_centered,
    )

__all__ = [
    "_next_power_of_two",
    "bbox_size_meters",
    "compute_world_params",
    "determine_is_projected",
    "local_crs_from_lonlat",
    "make_square_bounds_centered",
    "to_local_coords",
    "utm_crs_from_lonlat",
]
def __getattr__(name: str):
    """Lazily expose bounding-box helpers without triggering circular imports."""
    if name in {"_next_power_of_two", "bbox_size_meters", "compute_world_params", "make_square_bounds_centered"}:
        from osm2terrn.utils.geometry.bounds import (
            _next_power_of_two,
            bbox_size_meters,
            compute_world_params,
            make_square_bounds_centered,
        )

        mapping = {
            "_next_power_of_two": _next_power_of_two,
            "bbox_size_meters": bbox_size_meters,
            "compute_world_params": compute_world_params,
            "make_square_bounds_centered": make_square_bounds_centered,
        }
        return mapping[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
