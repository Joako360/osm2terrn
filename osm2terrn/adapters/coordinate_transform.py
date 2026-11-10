"""Project-level geospatial adapters used to transform OSM-derived data into local coordinates."""

from __future__ import annotations

import math
from typing import Any

from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from pyproj import CRS, Transformer
from shapely import affinity
from shapely.ops import transform as shapely_transform

from osm2terrn.utils.geometry.crs import local_crs_from_lonlat
from osm2terrn.utils.logger import get_logger, log_error

logger = get_logger("coordinate_transform")


def data_from_gdf(gdf: GeoDataFrame) -> dict[str, Any]:
    """Extract coarse offsets and dimensions from a GeoDataFrame."""
    if "lat" not in gdf or "lon" not in gdf:
        log_error(logger, "GeoDataFrame must contain 'lat' and 'lon' columns.")
        raise ValueError("GeoDataFrame must contain 'lat' and 'lon' columns.")

    return {
        "lat": gdf["lat"].iloc[0],
        "lon": gdf["lon"].iloc[0],
        "x_0": gdf.bounds.minx.iloc[0],
        "y_0": gdf.bounds.maxy.iloc[0],
        "x_size": float(gdf.bounds.maxx.iloc[0] - gdf.bounds.minx.iloc[0]),
        "y_size": float(gdf.bounds.maxy.iloc[0] - gdf.bounds.miny.iloc[0]),
        "area": gdf,
    }


def translate_gdf(gdf: GeoDataFrame, x_0: float = 0.0, y_0: float = 0.0) -> GeoDataFrame:
    """Translate a GeoDataFrame by offsets in projected coordinates."""
    if gdf is None or gdf.empty:
        log_error(logger, "GeoDataFrame must have a valid CRS and cannot be empty.")
        return gdf

    translated = gdf.copy()
    translated["geometry"] = translated["geometry"].apply(
        lambda geometry: affinity.translate(geometry, xoff=-x_0, yoff=-y_0)
    )
    return translated


def transform_gdf_to_crs(gdf: GeoDataFrame, target_crs: Any) -> GeoDataFrame:
    """Project a GeoDataFrame to the supplied CRS."""
    if gdf is None or gdf.empty:
        log_error(logger, "GeoDataFrame must have a valid CRS and cannot be empty.")
        return gdf
    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a valid CRS before projection")
    return gdf.to_crs(target_crs)


def transform_gdf_to_ror(gdf: GeoDataFrame, origin_lon: float, origin_lat: float) -> GeoDataFrame:
    """Project a GeoDataFrame into local Rigs of Rods coordinates."""
    local_crs = local_crs_from_lonlat(origin_lon, origin_lat)
    return transform_gdf_to_crs(gdf, local_crs)


def translate_graph(graph: MultiDiGraph, x_0: float, y_0: float) -> MultiDiGraph:
    """Translate graph node coordinates by offsets in projected coordinates."""
    translated = graph.copy()
    translated.graph["x_0"] = x_0
    translated.graph["y_0"] = y_0
    for node in translated.nodes():
        translated.nodes[node]["x"] = translated.nodes[node].get("x", 0.0) - x_0
        translated.nodes[node]["y"] = translated.nodes[node].get("y", 0.0) - y_0
    return translated


def transform_graph(graph: MultiDiGraph, target_crs: Any) -> MultiDiGraph:
    """Project graph node coordinates and edge geometries to target_crs."""
    if graph is None or len(graph.nodes) == 0:
        raise ValueError("Graph must be non-empty to transform")

    src_crs = graph.graph.get("crs")
    if src_crs is None:
        raise ValueError("Graph CRS is required before coordinate transformation")
    source = CRS.from_user_input(src_crs)
    target = CRS.from_user_input(target_crs)
    transformer = Transformer.from_crs(source, target, always_xy=True)
    transformed = graph.copy()
    if not isinstance(transformed, MultiDiGraph):
        transformed = MultiDiGraph(transformed)

    for _, node_data in transformed.nodes(data=True):
        if "x" not in node_data or "y" not in node_data:
            raise ValueError("Every graph node must have x and y coordinates")
        x_new, y_new = transformer.transform(node_data["x"], node_data["y"], errcheck=True)
        if not math.isfinite(float(x_new)) or not math.isfinite(float(y_new)):
            raise ValueError("Coordinate transformation produced non-finite node coordinates")
        node_data["x"] = float(x_new)
        node_data["y"] = float(y_new)

    def transform_coordinate(x, y, z=None):
        x_new, y_new = transformer.transform(x, y, errcheck=True)

        def values_are_finite(values) -> bool:
            try:
                iterator = iter(values)
            except TypeError:
                return math.isfinite(float(values))
            return all(math.isfinite(float(value)) for value in iterator)

        if not values_are_finite(x_new) or not values_are_finite(y_new):
            raise ValueError("Coordinate transformation produced non-finite edge coordinates")
        return (x_new, y_new) if z is None else (x_new, y_new, z)

    for _, _, _, edge_data in transformed.edges(keys=True, data=True):
        geometry = edge_data.get("geometry")
        if geometry is not None:
            edge_data["geometry"] = shapely_transform(
                transform_coordinate,
                geometry,
            )

    transformed.graph["crs"] = target
    return transformed


def transform_graph_to_ror(graph: MultiDiGraph, origin_lon: float, origin_lat: float) -> MultiDiGraph:
    """Project a graph into local Rigs of Rods coordinates."""
    local_crs = local_crs_from_lonlat(origin_lon, origin_lat)
    return transform_graph(graph, local_crs)
