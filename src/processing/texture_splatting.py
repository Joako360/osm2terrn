import numpy as np
from PIL import Image
from typing import Optional, Tuple
from utils.logger import get_logger, log_info, log_error, log_warning
from utils.constants import map_geometries

logger = get_logger("texture_splatting")

def create_texture_splat(
    elevation_data: np.ndarray,
    land_use_data: np.ndarray,  # This would be a rasterized land use map
    output_path: str,
    texture_map_size: Tuple[int, int] = (1024, 1024),
    texture_weights: Optional[dict] = None,  # type: ignore
) -> None:
    """
    Generates a texture splat map based on elevation and land use data.

    Args:
        elevation_data (np.ndarray): 2D numpy array of elevation values.
        land_use_data (np.ndarray): 2D numpy array of rasterized land use categories.
                                    (e.g., 1 for forest, 2 for water, 3 for urban, etc.)
        output_path (str): Path to save the generated splat map image (e.g., 'splat_map.png').
        texture_map_size (Tuple[int, int]): Desired output size of the splat map (width, height).
        texture_weights (dict): A dictionary mapping land use categories (integers) to
                                a tuple of (R, G, B, A) weights for different textures.
                                Each value should be between 0 and 255.
                                Example: {1: (255, 0, 0, 0), 2: (0, 255, 0, 0)}
                                If None, a default simple weighting is applied.
    """
    if elevation_data is None or land_use_data is None:
        log_error(logger, "Elevation or land use data is missing for texture splatting.")
        return

    if elevation_data.shape != land_use_data.shape:
        log_warning(logger, "Elevation and land use data shapes do not match. Resizing land use data.")
        # Use PIL for more accurate resizing with interpolation
        land_use_img = Image.fromarray(land_use_data.astype(np.uint8), mode='L')
        land_use_img = land_use_img.resize(elevation_data.shape[::-1], Image.Resampling.NEAREST)
        land_use_data = np.array(land_use_img)
        log_info(logger, "Land use data resized to match elevation data.")

    # Map land use categories to raster values
    # Example: suppose your raster uses 1 for parks, 2 for lakes, 3 for buildings
    land_use_category_map = {
        'parks': 1,
        'lakes': 2,
        'buildings': 3,
    }

    # Default texture weights if not provided
    if texture_weights is None:
        log_info(logger, "Using default texture weights based on map_geometries.")
        texture_weights = {
            land_use_category_map['parks']: (0, 255, 0, 0),      # Green for parks
            land_use_category_map['lakes']: (0, 0, 255, 0),      # Blue for lakes
            land_use_category_map['buildings']: (255, 0, 0, 0),  # Red for buildings
            0: (0, 0, 0, 0)  # Default for unknown/no category
        }

    # Check if the input arrays are 2D
    if elevation_data.ndim != 2 or land_use_data.ndim != 2:
        log_error(logger, "Input arrays must be 2D.")
        return

    # Initialize an empty RGBA image for the splat map
    splat_map = np.zeros((*elevation_data.shape, 4), dtype=np.uint8)

    # Apply texture weights based on land use data
    for category, weights in texture_weights.items():
        mask = (land_use_data == category)
        splat_map[mask, 0] = weights[0]  # Red
        splat_map[mask, 1] = weights[1]  # Green
        splat_map[mask, 2] = weights[2]  # Blue
        splat_map[mask, 3] = weights[3]  # Alpha

    # Resize the splat map to the desired output size
    # Using PIL for resizing as it handles image interpolation well
    splat_image = Image.fromarray(splat_map, 'RGBA')
    splat_image = splat_image.resize(texture_map_size, Image.Resampling.LANCZOS)

    # Save the splat map
    try:
        splat_image.save(output_path)
        log_info(logger, f"Texture splat map saved to {output_path}")
    except Exception as e:
        log_error(logger, f"Failed to save texture splat map to {output_path}: {e}")
        return
