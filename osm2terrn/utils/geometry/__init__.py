"""Generic geometry utilities reusable across projects."""

from osm2terrn.utils.geometry.bounds import (
    _next_power_of_two,
    bbox_size_meters,
    compute_world_params,
    make_square_bounds_centered,
)
from osm2terrn.utils.geometry.crs import (
    determine_is_projected,
    local_crs_from_lonlat,
    to_local_coords,
    utm_crs_from_lonlat,
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
