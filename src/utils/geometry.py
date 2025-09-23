from math import ceil
from typing import Any
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from osmnx import project_graph
from osmnx.projection import project_gdf
from shapely import affinity
from utils.logger import get_logger, log_error

logger = get_logger("geometry")


def data_from_gdf(gdf: GeoDataFrame) -> dict[str, Any]:
    """
    Extracts offset, size, and area information from a GeoDataFrame.

    Args:
        gdf (GeoDataFrame): Input GeoDataFrame with 'lat' and 'lon' columns.

    Returns:
        dict: Dictionary with latitude, longitude, offsets, sizes, and area.
    """
    if 'lat' not in gdf or 'lon' not in gdf:
        log_error(logger, "GeoDataFrame must contain 'lat' and 'lon' columns.")
        raise ValueError("GeoDataFrame must contain 'lat' and 'lon' columns.")
    d = {
        'lat': gdf['lat'].iloc[0],
        'lon': gdf['lon'].iloc[0],
        'x_0': gdf.bounds.minx.iloc[0],
        'y_0': gdf.bounds.maxy.iloc[0],
        'x_size': ceil(gdf.bounds.maxx.iloc[0] - gdf.bounds.minx.iloc[0]),
        'y_size': ceil(gdf.bounds.maxy.iloc[0] - gdf.bounds.miny.iloc[0]),
        'world_size': ceil(max(gdf.bounds.maxx.iloc[0] - gdf.bounds.minx.iloc[0], gdf.bounds.maxy.iloc[0] - gdf.bounds.miny.iloc[0])),
        'area': gdf
    }
    return d


def translate_gdf(gdf: GeoDataFrame, x_0: float = 0., y_0: float = 0.) -> GeoDataFrame:
    """
    Translates a GeoDataFrame to new coordinates with x_0, y_0 as the new origin.

    Args:
        gdf (GeoDataFrame): Input GeoDataFrame.
        x_0 (float, optional): X offset. Defaults to minx of gdf.
        y_0 (float, optional): Y offset. Defaults to maxy of gdf.

    Returns:
        GeoDataFrame: Translated GeoDataFrame.
    """
    if x_0 is None:
        x_0 = gdf.bounds.minx.iloc[0]
    if y_0 is None:
        y_0 = gdf.bounds.maxy.iloc[0]
    gdf_trns = gdf.copy()
    gdf_trns['geometry'] = gdf_trns['geometry'].apply(lambda geom: affinity.translate(geom, xoff=-x_0, yoff=-y_0))
    return gdf_trns


def translate_graph(G: MultiDiGraph, x_0: float, y_0: float) -> MultiDiGraph:
    """
    Translates all node coordinates in a MultiDiGraph by given offsets.

    Args:
        G (MultiDiGraph): Input graph.
        x_0 (float): X offset.
        y_0 (float): Y offset.

    Returns:
        MultiDiGraph: Translated graph.
    """
    G_trns = G.copy()
    G_trns.graph['x_0'] = x_0
    G_trns.graph['y_0'] = y_0
    for node in G_trns.nodes():
        G_trns.nodes[node]['x'] = G_trns.nodes[node].get('x', 0.0) - x_0
        G_trns.nodes[node]['y'] = G_trns.nodes[node].get('y', 0.0) - y_0
    return G_trns # type: ignore


def transform_gdf(gdf: GeoDataFrame, x_0: float = 0., y_0: float = 0.) -> GeoDataFrame:
    """
    Projects and translates a GeoDataFrame to a new coordinate system.

    Args:
        gdf (GeoDataFrame): Input GeoDataFrame.
        x_0 (float, optional): X offset.
        y_0 (float, optional): Y offset.

    Returns:
        GeoDataFrame: Projected and translated GeoDataFrame.
    """
    if len(gdf['geometry']) != 0:
        gdf_proj = project_gdf(gdf)
        gdf_trns = translate_gdf(gdf_proj, x_0, y_0)
        return gdf_trns
    else:
        log_error(logger, "GeoDataFrame must have a valid CRS and cannot be empty.")
        return gdf


def transform_graph(G: MultiDiGraph, x_0: float, y_0: float) -> MultiDiGraph:
    """
    Projects and translates a MultiDiGraph to a new coordinate system.

    Args:
        G (MultiDiGraph): Input graph.
        x_0 (float): X offset.
        y_0 (float): Y offset.

    Returns:
        MultiDiGraph: Projected and translated graph.
    """
    G_proj = project_graph(G)
    # Ensure the result is a MultiDiGraph
    if not isinstance(G_proj, MultiDiGraph):
        G_proj = MultiDiGraph(G_proj)
    G_trns = translate_graph(G_proj, x_0, y_0)
    return G_trns
