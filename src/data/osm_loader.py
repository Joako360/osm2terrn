import networkx as nx
import osmnx as ox
from shapely.geometry import LineString
from typing import Dict, List, Optional, Tuple, Union
from pyproj import CRS
from utils.logger import get_logger, log_info, log_warning
from utils.bbox import BBox

logger = get_logger("osm_loader")
LineStringWithAttrs = List[Tuple[LineString, Dict]]

def load_graph(
    place: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    network_type: str = "drive",
    simplify: bool = True,
) -> nx.MultiDiGraph:
    """
    Load a graph from OSM data.

    Args:
        place: Name of the place to load (e.g., "Berkeley, CA").
        bbox: Bounding box as (north, south, east, west).
        network_type: Type of network to load (e.g., "drive").
        simplify: Whether to simplify the graph.

    Returns:
        NetworkX directed graph projected to metric coordinates.
    """
    if place is None and bbox is None:
        log_warning(logger, "Neither place nor bbox provided")
        raise ValueError("You must specify 'place' or 'bbox'.")

    if place is not None:
        G = ox.graph_from_place(place, network_type=network_type, simplify=simplify)
    else:
        assert bbox is not None
        G = ox.graph_from_bbox(bbox, network_type=network_type, simplify=simplify)

    # Project the graph to metric coordinates
    G = ox.project_graph(G)

    return G

def edges_to_lines(G: nx.MultiDiGraph) -> Tuple[LineStringWithAttrs, CRS]:
    # Convert to undirected to avoid duplicate edges for bidirectional roads
    G_undir = G.to_undirected()
    
    metric_crs = G.graph.get("crs", None)
    if metric_crs is None:
        # fallback if projection did not set CRS
        metric_crs = CRS.from_epsg(4326)
        log_warning(logger, "CRS not found in graph, defaulting to WGS84 (EPSG:4326)")
    geometries_with_attrs: LineStringWithAttrs = []
    for u, v, k, data in G_undir.edges(keys=True, data=True):
        if 'geometry' in data:
            geometry = data['geometry']
        else:
            p0 = (G_undir.nodes[u]['x'], G_undir.nodes[u]['y'])
            p1 = (G_undir.nodes[v]['x'], G_undir.nodes[v]['y'])
            geometry = LineString([p0, p1])
        geometries_with_attrs.append((geometry, dict(data)))
    return geometries_with_attrs, metric_crs
