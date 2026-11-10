import networkx as nx
import osmnx as ox
from shapely.geometry import LineString
from typing import Dict, List, Optional, Tuple, Union
from pyproj import CRS

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.utils.logger import get_logger, log_info, log_warning

logger = get_logger("osm_loader")
LineStringWithAttrs = List[Tuple[LineString, Dict]]
_GRAPH_CACHE_NAMESPACE = "providers/osm/graph"
_GRAPH_CACHE_ALGORITHM_VERSION = "1"

def load_graph(
    place: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    network_type: str = "drive",
    simplify: bool = True,
    bidirectional: bool = False,
) -> Union[nx.MultiDiGraph, nx.MultiGraph]:  # Cambiar tipo de retorno
    """
    Load a graph from OSM data.

    Args:
        place: Name of the place to load (e.g., "Berkeley, CA").
        bbox: Bounding box as (north, south, east, west).
        network_type: Type of network to load (e.g., "drive").
        simplify: Whether to simplify the graph.
        bidirectional: If True, convert to undirected graph to avoid duplicate edges.

    Returns:
        NetworkX graph (directed if bidirectional=False, undirected if True).
    """
    if place is None and bbox is None:
        log_warning(logger, "Neither place nor bbox provided")
        raise ValueError("You must specify 'place' or 'bbox'.")

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[Union[nx.MultiDiGraph, nx.MultiGraph]]()
    cache_key = cache_manager.build_key(
        {
            "place": place,
            "bbox": list(bbox) if bbox is not None else None,
            "network_type": network_type,
            "simplify": simplify,
            "bidirectional": bidirectional,
        },
        provider="osm",
        algorithm_version=_GRAPH_CACHE_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="osm_graph",
    )
    cached_graph = cache_manager.get(namespace=_GRAPH_CACHE_NAMESPACE, key=cache_key, serializer=serializer)
    if cached_graph is not None:
        log_info(logger, "Loaded OSM graph from cache.")
        return cached_graph[0]

    if place is not None:
        G = ox.graph_from_place(place, network_type=network_type, simplify=simplify)
    else:
        assert bbox is not None
        G = ox.graph_from_bbox(bbox, network_type=network_type, simplify=simplify)

    # Convert to undirected graph to avoid duplicate edges for bidirectional roads
    if bidirectional:
        log_info(logger, "Converting graph to undirected (bidirectional=True)")
        G = G.to_undirected()

    cache_manager.put(
        namespace=_GRAPH_CACHE_NAMESPACE,
        key=cache_key,
        value=G,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="osm_graph",
            provider="osm",
            algorithm_version=_GRAPH_CACHE_ALGORITHM_VERSION,
            format_version="1",
        ),
    )

    return G

def edges_to_lines(G: Union[nx.MultiDiGraph, nx.MultiGraph]) -> Tuple[LineStringWithAttrs, CRS]:  # Cambiar parámetro
    G_metric = ox.project_graph(G) # type: ignore
    metric_crs = G_metric.graph.get("crs", None)
    if metric_crs is None:
        # fallback if projection did not set CRS
        metric_crs = CRS.from_epsg(4326)
        log_warning(logger, "CRS not found in graph, defaulting to WGS84 (EPSG:4326)")
    geometries_with_attrs: LineStringWithAttrs = []
    for u, v, k, data in G_metric.edges(keys=True, data=True):
        if 'geometry' in data:
            geometry = data['geometry']
        else:
            p0 = (G_metric.nodes[u]['x'], G_metric.nodes[u]['y'])
            p1 = (G_metric.nodes[v]['x'], G_metric.nodes[v]['y'])
            geometry = LineString([p0, p1])
        attrs = dict(data)
        # Keep edge endpoints so downstream formatters can classify intersections.
        attrs["u"] = u
        attrs["v"] = v
        attrs["k"] = k
        geometries_with_attrs.append((geometry, attrs))
    return geometries_with_attrs, metric_crs

