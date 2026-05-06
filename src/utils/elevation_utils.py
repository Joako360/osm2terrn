# -*- coding: utf-8 -*-
"""
Elevation and water level utilities for realistic terrain generation.

This module provides functions to:
- Calculate realistic water levels based on elevation data and water features
- Dynamically scale terrain height based on actual elevation ranges
- Handle sea level references and water body detection
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any
import geopandas as gpd
from utils.logger import get_logger, log_info, log_warning, log_error

logger = get_logger("elevation_utils")

# Sea level reference (0 meters)
SEA_LEVEL = 0.0

# Default minimum height above water for terrain (to avoid complete submersion)
MIN_TERRAIN_HEIGHT_ABOVE_WATER = 10.0  # meters

# Water detection thresholds
WATER_ELEVATION_PERCENTILE = 5  # Percentile for detecting water level from elevation data


def detect_water_level(
    elevation_data: np.ndarray,
    water_features_gdf: Optional[gpd.GeoDataFrame] = None,
    min_elevation: float = 0.0,
    max_elevation: float = 100.0,
) -> float:
    """
    Detects the water level from elevation data.

    The water level is calculated as -min_elevation, which places sea level (0) as the reference.
    This ensures realistic terrain appearance where visible elevation matches actual differences.

    Formula: WaterLine = -min_elevation

    For example:
    - Terrain with elevation 45m-235m
    - WaterLine = -45m
    - Terrain appears from water level to 190m height (235-45=190)

    Args:
        elevation_data (np.ndarray): 2D array of elevation values in meters
        water_features_gdf (gpd.GeoDataFrame, optional): GeoDataFrame with water feature polygons (currently unused)
        min_elevation (float): Minimum elevation in the region (in meters)
        max_elevation (float): Maximum elevation in the region (in meters)

    Returns:
        float: Water level in meters (typically negative for lands above sea level)
    """
    try:
        # Water level is simply negative of minimum elevation
        # This makes sea level (0) the reference point
        water_level = -min_elevation

        log_info(logger, f"Water level: {water_level:.2f}m (min elevation: {min_elevation:.2f}m)")
        return float(water_level)

    except Exception as e:
        log_error(logger, f"Error detecting water level: {e}")
        return 0.0


def calculate_realistic_world_height(
    min_elevation: float,
    max_elevation: float,
) -> float:
    """
    Calculates WorldSizeY (vertical world size) based on actual elevation range.

    WorldSizeY represents the vertical extent of the terrain and is simply the difference
    between maximum and minimum elevation. This ensures the terrain height matches real
    topography in Rigs of Rods.

    Formula: WorldSizeY = max_elevation - min_elevation

    Args:
        min_elevation (float): Minimum elevation in the region (in meters)
        max_elevation (float): Maximum elevation in the region (in meters)

    Returns:
        float: WorldSizeY value in meters
    """
    try:
        # Calculate the natural elevation range directly
        world_height = max_elevation - min_elevation

        # Ensure minimum height for the terrain (some terrains are very flat)
        min_world_height = 50.0  # Minimum 50 meters
        if world_height < min_world_height:
            log_warning(logger, f"Elevation range {world_height:.2f}m is very small; using minimum {min_world_height}m")
            world_height = min_world_height

        # Cap at a reasonable maximum (to prevent extreme stretching)
        max_world_height = 10000.0  # Maximum 10 km
        if world_height > max_world_height:
            log_warning(logger, f"Elevation range {world_height:.2f}m exceeds maximum; capping at {max_world_height}m")
            world_height = max_world_height

        log_info(
            logger,
            f"Calculated WorldSizeY: {world_height:.2f}m from elevation range "
            f"{min_elevation:.2f}m - {max_elevation:.2f}m",
        )
        return world_height

    except Exception as e:
        log_error(logger, f"Error calculating world height: {e}")
        return 300.0  # Fallback to default


def calculate_water_bottom_line(
    water_level: float,
    water_depth: float = 150.0,
) -> float:
    """
    Calculates the water bottom line (depth of water below surface).

    The water bottom is simply the water surface level minus the depth.

    Formula: WaterBottomLine = water_level - water_depth

    Example:
    - WaterLine = -45m
    - Water depth = 150m
    - WaterBottomLine = -45 - 150 = -195m

    Args:
        water_level (float): Water surface level in meters
        water_depth (float): Depth of water below surface in meters (default: 150m)

    Returns:
        float: Water bottom line elevation in meters
    """
    bottom_line = water_level - water_depth
    log_info(logger, f"Water bottom line: {bottom_line:.2f}m (surface: {water_level:.2f}m, depth: {water_depth:.2f}m)")
    return bottom_line


def compute_elevation_normalization_params(
    elevation_data: np.ndarray,
    min_elevation: float,
    max_elevation: float,
) -> Tuple[float, float]:
    """
    Computes normalization parameters for heightmap generation.

    Returns the actual min/max elevations from the data, handling NaN values appropriately.

    Args:
        elevation_data (np.ndarray): Raw elevation array from API
        min_elevation (float): Expected minimum elevation
        max_elevation (float): Expected maximum elevation

    Returns:
        Tuple[float, float]: (normalized_min, normalized_max) for heightmap scaling
    """
    try:
        valid_data = elevation_data[~np.isnan(elevation_data)]

        if valid_data.size == 0:
            log_warning(logger, "No valid elevation data for normalization")
            return 0.0, 1.0

        actual_min = float(np.nanmin(elevation_data))
        actual_max = float(np.nanmax(elevation_data))

        # Clamp to expected range with small tolerance
        tolerance = 0.1
        norm_min = max(actual_min, min_elevation - tolerance)
        norm_max = min(actual_max, max_elevation + tolerance)

        if norm_min >= norm_max:
            log_warning(logger, "Elevation range is invalid; using full data range")
            return actual_min, actual_max

        log_info(logger, f"Normalization range: {norm_min:.2f}m to {norm_max:.2f}m")
        return norm_min, norm_max

    except Exception as e:
        log_error(logger, f"Error computing normalization parameters: {e}")
        return 0.0, 1.0


def prepare_water_config(
    elevation_data: np.ndarray,
    min_elevation: float,
    max_elevation: float,
    water_features_gdf: Optional[gpd.GeoDataFrame] = None,
) -> Dict[str, float]:
    """
    Prepares a complete water configuration dict for terrain export.

    This function integrates all water-related calculations into a single config dict
    that can be passed directly to terrain exporters.

    Args:
        elevation_data (np.ndarray): Elevation data array
        min_elevation (float): Minimum elevation in meters
        max_elevation (float): Maximum elevation in meters
        water_features_gdf (gpd.GeoDataFrame, optional): Water features from OSM

    Returns:
        Dict[str, float]: Water configuration with keys:
            - 'enabled': bool (always True for now)
            - 'water_line': float (water surface level in meters)
            - 'water_bottom_line': float (water bottom in meters)
    """
    try:
        # Detect water level
        water_level = detect_water_level(
            elevation_data,
            water_features_gdf,
            min_elevation,
            max_elevation,
        )

        # Calculate water bottom
        water_bottom = calculate_water_bottom_line(water_level)

        config = {
            "enabled": True,
            "water_line": water_level,
            "water_bottom_line": water_bottom,
        }

        log_info(logger, f"Water config prepared: {config}")
        return config

    except Exception as e:
        log_error(logger, f"Error preparing water config: {e}")
        # Return safe defaults
        return {
            "enabled": False,
            "water_line": 0.0,
            "water_bottom_line": -150.0,
        }
