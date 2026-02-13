import networkx as nx
import osmnx as ox
from shapely.geometry import LineString
from typing import Optional, Tuple, Dict, List
from pyproj import CRS
from utils.logger import get_logger, log_info, log_warning
from utils.bbox import BBox

logger = get_logger("osm_loader")
LineStringWithAttrs = List[Tuple[LineString, Dict]]

def load_graph(place: Optional[str] = None, bbox: Optional[Tuple[float, float, float, float]] = None, network_type: str = "drive") -> nx.MultiDiGraph:
    if place:
        log_info(logger, f"Loading graph for place: {place}")
        return ox.graph_from_place(place, network_type=network_type, simplify=True)
    if bbox:
        log_info(logger, f"Loading graph for bbox: {bbox}")
        # accept bbox-like inputs (tuple, list or BBox). Use BBox to parse and validate.
        try:
            bbox_obj = BBox(bbox)
        except Exception as e:
            log_warning(logger, f"Invalid bbox provided to load_graph: {e}")
            raise
        # If projected, reproject to geographic for osmnx
        if getattr(bbox_obj, "is_projected", False):
            try:
                bbox_geo = bbox_obj.reproject("EPSG:4326")
                bbox_obj = bbox_geo
                log_info(logger, "Reprojected bbox to EPSG:4326 for osmnx.graph_from_bbox.")
            except Exception as e:
                log_warning(logger, f"Could not reproject bbox for osmnx: {e} — proceeding with original bbox (may be incorrect).")
        # osmnx.graph_from_bbox expects (north, south, east, west)
        north, south, east, west = bbox_obj.north, bbox_obj.south, bbox_obj.east, bbox_obj.west
        G = ox.graph_from_bbox((north, south, east, west), network_type=network_type, simplify=True, truncate_by_edge=True)
        log_info(logger, "Graph loaded and clipped strictly to bounding box.")
        return G
    log_warning(logger, "Neither place nor bbox provided")
    raise ValueError("You must specify 'place' or 'bbox'.")

def edges_to_lines(G: nx.MultiDiGraph) -> Tuple[LineStringWithAttrs, CRS]:
    G_metric = ox.project_graph(G)
    metric_crs = G_metric.graph.get("crs", None)
    if metric_crs is None:
        # Fallback to WGS84 if projection failed
        metric_crs = CRS.from_epsg(4326)
        log_warning(logger, "CRS not found in graph, defaulting to WGS84 (EPSG:4326)")
    geometries_with_attrs: LineStringWithAttrs = []
    for u, v, k, data in G_metric.edges(keys=True, data=True):
        if 'geometry' in data:
            geometry = data['geometry']
        else:
            point0 = (G_metric.nodes[u]['x'], G_metric.nodes[u]['y'])
            point1 = (G_metric.nodes[v]['x'], G_metric.nodes[v]['y'])
            geometry = LineString([point0, point1])
        geometries_with_attrs.append((geometry, dict(data)))
    return geometries_with_attrs, metric_crs
