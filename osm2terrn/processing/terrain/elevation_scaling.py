"""Terrain elevation scaling utilities used by runtime generation workflows."""

from __future__ import annotations

from typing import Optional

from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_error, log_info

logger = get_logger("elevation_scaling")
_PROGRAM_CONFIG = get_program_config()


def calculate_world_size_y(
    min_elevation: Optional[float] = None,
    max_elevation: Optional[float] = None,
    default_height: Optional[float] = None,
) -> float:
    """Calculate vertical terrain size from elevation stats while preserving runtime limits."""
    resolved_default_height = (
        _PROGRAM_CONFIG.elevation_runtime.default_world_size_y
        if default_height is None
        else default_height
    )
    if (
        not _PROGRAM_CONFIG.elevation_runtime.enable_realistic_elevation
        or min_elevation is None
        or max_elevation is None
    ):
        return resolved_default_height

    try:
        world_height = max_elevation - min_elevation
        world_height = max(world_height, _PROGRAM_CONFIG.elevation_runtime.min_world_size_y)
        world_height = min(world_height, _PROGRAM_CONFIG.elevation_runtime.max_world_size_y)
        log_info(
            logger,
            (
                f"Calculated WorldSizeY: {world_height:.2f}m from elevation range "
                f"{min_elevation:.2f}m - {max_elevation:.2f}m"
            ),
        )
        return world_height
    except Exception as exc:
        log_error(logger, f"Error calculating world height: {exc}; using default {resolved_default_height}m")
        return resolved_default_height
