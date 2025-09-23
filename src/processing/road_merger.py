from collections import defaultdict, Counter
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import linemerge
from typing import Dict, List, Tuple
from utils.logger import get_logger, log_warning

logger = get_logger("road_merger")
LineStringWithAttrs = List[Tuple[LineString, Dict]]

def merge_by_highway(geoms_attrs: LineStringWithAttrs) -> LineStringWithAttrs:
    """
    Merge LineString geometries by their 'highway' attribute.

    Groups input LineStrings by the 'highway' key in their attributes, merges geometries within each group,
    and returns a list of merged LineStrings with their associated highway type.

    Args:
        geoms_attrs (LineStringWithAttrs): List of tuples (LineString, attributes dict).

    Returns:
        LineStringWithAttrs: List of tuples (merged LineString, {'highway': key}).
    """
    buckets: Dict[str, LineStringWithAttrs] = defaultdict(list)
    for geom, attrs in geoms_attrs:
        hw = attrs.get("highway")
        key = hw if isinstance(hw, str) else (hw[0] if isinstance(hw, list) and hw else "unknown")
        buckets[str(key)].append((geom, attrs))
    merged: LineStringWithAttrs = []
    for key, items in buckets.items():
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
            merged.append((merged_line, {"highway": key, "name": name, "bridge": is_bridge}))
        elif isinstance(merged_line, MultiLineString):
            for part in merged_line.geoms:
                if isinstance(part, LineString):
                    merged.append((part, {"highway": key, "name": name, "bridge": is_bridge}))
                else:
                    log_warning(logger, f"Non-LineString geometry found in MultiLineString for highway '{key}'.")
        else:
            log_warning(logger, f"Unexpected geometry type '{type(merged_line)}' encountered during merging.")
    return merged
