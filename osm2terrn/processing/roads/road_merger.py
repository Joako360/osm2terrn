from collections import defaultdict, Counter
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
from typing import Dict, List, Tuple
from osm2terrn.utils.logger import get_logger, log_warning, log_info

logger = get_logger("road_merger")
LineStringWithAttrs = List[Tuple[LineString, Dict]]


def _normalize_direction(attrs: Dict) -> str:
    """
    Return a normalized direction key for deduplication.
    Returns 'forward', 'backward', or 'both' based on oneway attribute.
    """
    oneway = attrs.get("oneway", "")
    if isinstance(oneway, bool):
        return "forward" if oneway else "both"
    oneway_str = str(oneway).lower()
    if oneway_str in ("yes", "true", "1", "y"):
        return "forward"
    if oneway_str in ("-1", "reverse"):
        return "backward"
    return "both"


def merge_by_highway(geoms_attrs: LineStringWithAttrs, merge_by_name: bool = True) -> LineStringWithAttrs:
    """
    Merge LineString geometries by highway type and optionally by street name.

    Args:
        geoms_attrs: List of tuples (LineString, attributes dict).
        merge_by_name: If True, group also by street name to avoid segmenting
                      streets unnecessarily. Default True.

    Returns:
        LineStringWithAttrs: List of tuples (merged LineString, merged attributes).
    """
    # First, deduplicate reverse-direction edges (bidirectional roads stored as A→B and B→A)
    seen_edges: Dict[Tuple, Tuple[LineString, Dict]] = {}
    for geom, attrs in geoms_attrs:
        coords = tuple(geom.coords)
        if len(coords) >= 2:
            # Create a canonical edge key (min, max) to detect reverse duplicates
            edge_key = (coords[0], coords[-1])
            direction = _normalize_direction(attrs)
            if direction == "both":
                # For bidirectional roads, keep only one direction
                reverse_key = (coords[-1], coords[0])
                if reverse_key in seen_edges:
                    # Skip this edge, already have the reverse
                    continue
            seen_edges[edge_key] = (geom, attrs)

    deduped: LineStringWithAttrs = list(seen_edges.values())
    log_info(logger, f"After deduplication: {len(deduped)} edges from {len(geoms_attrs)} original")

    # Group by highway type (and optionally by name)
    buckets: Dict[str, LineStringWithAttrs] = defaultdict(list)
    for geom, attrs in deduped:
        hw = attrs.get("highway")
        key = hw if isinstance(hw, str) else (hw[0] if isinstance(hw, list) and hw else "unknown")

        if merge_by_name:
            # Also group by street name to keep continuous roads together
            name = attrs.get("name")
            if name:
                key = f"{key}|{name}"  # Composite key

        buckets[key].append((geom, attrs))

    merged: LineStringWithAttrs = []
    for key, items in buckets.items():
        # Parse highway type from key (may include name)
        highway_type = key.split("|")[0] if "|" in key else key

        lines = [g for g, _ in items]
        # derive a representative OSM name if present
        names = [str(attrs.get("name")).strip() for _, attrs in items if attrs.get("name")]
        # if any part has bridge=yes, mark the merged segment as a bridge
        is_bridge = any(str(attrs.get("bridge", "no")).lower() in ("yes", "true", "1") for _, attrs in items)
        name = None
        if names:
            # pick most common name
            name = Counter(names).most_common(1)[0][0]

        merged_line = linemerge(lines)
        if isinstance(merged_line, LineString):
            merged.append((merged_line, {"highway": highway_type, "name": name, "bridge": is_bridge}))
        elif isinstance(merged_line, MultiLineString):
            for part in merged_line.geoms:
                if isinstance(part, LineString):
                    merged.append((part, {"highway": highway_type, "name": name, "bridge": is_bridge}))
                else:
                    log_warning(logger, f"Non-LineString geometry found in MultiLineString for highway '{highway_type}'.")
        else:
            log_warning(logger, f"Unexpected geometry type '{type(merged_line)}' encountered during merging.")

    log_info(logger, f"Merged into {len(merged)} road segments from {len(buckets)} groups")
    return merged
