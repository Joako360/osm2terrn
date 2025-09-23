
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import requests
import rasterio
from PIL import Image
import scipy.ndimage

from io import BytesIO
from typing import Dict, Tuple, Optional
from math import ceil, inf
from utils.constants import EARTH_MAX_ELEVATION, EARTH_MIN_ELEVATION
from utils.logger import get_logger, log_info, log_error, log_warning

logger = get_logger("heightmap_handler")

def fetch_elevation_from_api(bounds: gpd.GeoDataFrame) -> tuple[np.ndarray, float, float]:
    """
    Fetches elevation data from the OpenTopography API and returns an elevation matrix along with the minimum and maximum elevations.

    This function performs an HTTP request to the OpenTopography API using the geographic coordinate parameters
    (north, south, east, west) to obtain an elevation file in GeoTIFF format. The elevation matrix is processed to
    handle `nodata` values and the minimum and maximum elevation of the requested region is calculated.

    Parameters:
    -----------
    bounds : gpd.GeoDataFrame
        A GeoDataFrame with the coordinates of the region of interest, with the following keys:
        - 'xmin' (float): western boundary coordinate.
        - 'ymin' (float): South boundary coordinate.
        - 'xmax' (float): East boundary coordinate.
        - 'ymax' (float): coordinate of the north boundary.

    Return:
    --------
    elevation : numpy.ndarray
        2D array with elevation data (in meters) for the requested region.
    
    if api_key and len(api_key) > 6:
        masked = api_key[:3] + "..." + api_key[-3:]
    else:
        masked = "(invalid or missing)"
    log_info(logger, f"Using OpenTopography API Key: {masked}")
        The maximum elevation in the requested region (in meters).
    
    min_elev : float
        The minimum elevation in the requested region (in meters).

    Exceptions:
    ------------
    Throws an exception if the HTTP response is unsuccessful (code other than 200).
    """
    from utils.constants import get_opentopo_elevation_api_key
    api_key = get_opentopo_elevation_api_key()
    # Mask API key for logging
    if api_key and len(api_key) > 6:
        masked = api_key[:3] + "..." + api_key[-3:]
    else:
        masked = "(invalid or missing)"
    log_info(logger, f"Using OpenTopography API Key: {masked}")
    url = 'https://portal.opentopography.org/API/globaldem'
    west, south, east, north = bounds.bounds.loc[0].values
    params = {
        'demtype': 'AW3D30',
        'west': west,
        'south': south,
        'east': east,
        'north': north,
        'outputFormat': 'GTiff',
        'API_Key': api_key
    }
    try:
        res = requests.get(url, params=params, stream=True)
        res.raise_for_status()
        log_info(logger, "Elevation data downloaded successfully.")
        with BytesIO(res.content) as f:
            with rasterio.open(f) as dataset:
                elevation = dataset.read(1)
                nodata_value = dataset.nodata
                if nodata_value is not None:
                    elevation = np.where(elevation == nodata_value, np.nan, elevation)
                maxh = np.nanmax(elevation)
                minh = np.nanmin(elevation)
                log_info(logger, f"Elevation min: {minh} m, max: {maxh} m")
                return elevation, maxh, minh
    except Exception as e:
        log_error(logger, f"Failed to fetch elevation data: {e}")
        raise

def plot_elevation_map(elevation: np.ndarray, cmap: str = "gray", vmin: float = 0., vmax: float = 1.) -> None:
    """
    Displays the elevation map using matplotlib without saving the figure.

    Args:
        elevation (np.ndarray): Elevation array.
        cmap (str): Colormap for the map.
        vmin (float): Minimum value for normalization.
        vmax (float): Maximum value for normalization.
    """
    if elevation.size == 0:
        log_error(logger, "Elevation array is empty. Skipping plot.")
        return
    plt.figure(figsize=(10, 6))
    plt.imshow(elevation, cmap=cmap, vmin=vmin, vmax=vmax)
    plt.colorbar(label="Elevation (m)")
    plt.title("Elevation Map")
    plt.axis("off")
    plt.show()
    plt.close()
    log_info(logger, "Elevation map displayed.")

def generate_heightmap_n_texture(
    bounds: gpd.GeoDataFrame,
    heightmap_path: str = "heightmap.png",
    groundmap_path: str = "groundmap.png",
    cmap_name: str = "gist_earth",
    output_size: tuple[int, int] = (1024, 1024),
    smoothing_sigma: float = 1.0,
    elevation_data: Optional[dict] = None
) -> None:
    """
    Generates and saves both the grayscale heightmap and colored ground texture using a matplotlib colormap,
    with optional rescaling and smoothing.

    Args:
        bounds (gpd.GeoDataFrame): GeoDataFrame with the region bounds.
        heightmap_path (str): Path to save the grayscale heightmap PNG.
        groundmap_path (str): Path to save the colored ground texture PNG.
        cmap_name (str): Name of the matplotlib colormap to use for ground texture.
        output_size (tuple[int, int]): Output image size (width, height).
        smoothing_sigma (float): Sigma for Gaussian smoothing.
    """
    if bounds is None or bounds.empty:
        log_warning(logger, "No map data available.")
        return

    if elevation_data and 'elevation' in elevation_data and 'maxh' in elevation_data and 'minh' in elevation_data:
        elevation = elevation_data['elevation']
        maxh = elevation_data['maxh']
        minh = elevation_data['minh']
        elevation_normalized = ((elevation - minh) / (maxh - minh))
        elevation_normalized = np.nan_to_num(elevation_normalized, nan=0.0)
    else:
        try:
            elevation, maxh, minh = fetch_elevation_from_api(bounds)
            elevation_normalized = ((elevation - minh) / (maxh - minh))
            elevation_normalized = np.nan_to_num(elevation_normalized, nan=0.0)
        except Exception as e:
            # Fallback: flat terrain so the export can proceed
            log_warning(logger, f"Falling back to flat heightmap due to elevation fetch failure: {e}")
            w, h = output_size
            elevation_normalized = np.zeros((h, w), dtype=np.float32)

    # Smoothing
    elevation_smoothed = scipy.ndimage.gaussian_filter(elevation_normalized, sigma=smoothing_sigma)

    # Rescaling
    img_heightmap = Image.fromarray((elevation_smoothed * 255).astype(np.uint8), mode='L')
    img_heightmap = img_heightmap.resize(output_size, Image.Resampling.LANCZOS)
    img_heightmap.save(heightmap_path)
    log_info(logger, f"Heightmap saved to: {heightmap_path}")

    # Ground texture (colormap)
    cmap = plt.get_cmap(cmap_name)
    colored = cmap(elevation_smoothed)[:, :, :3]
    colored_uint8 = (colored * 255).astype(np.uint8)
    img_groundmap = Image.fromarray(colored_uint8, mode="RGB")
    img_groundmap = img_groundmap.resize(output_size, Image.Resampling.LANCZOS)
    img_groundmap.save(groundmap_path)
    log_info(logger, f"Ground texture saved to: {groundmap_path}")