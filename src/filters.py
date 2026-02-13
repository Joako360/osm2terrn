# osm2terrn/filters.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple
from shapely.geometry import LineString

Edge = Tuple[LineString, Dict]

@dataclass
class FilterConfig:
    """
    Declarative filtering for OSM edges → keep a clean subset before merging/densifying.
    
    Attributes:
        include_highway: Highway types to keep.
        exclude_highway: Highway types to discard.
        include_surface: Surface types to keep.
        exclude_surface: Surface types to discard.
        exclude_access: Access values to discard.
        min_lanes: Minimum number of lanes.
        max_lanes: Maximum number of lanes.
        only_oneway: Keep only oneway roads.
        exclude_oneway: Exclude oneway roads.
        min_length_m: Minimum segment length in meters.
        max_length_m: Maximum segment length in meters.
    
    All sets are case-insensitive; values are normalized to lowercase strings.
    If a set is empty or None, that criterion is ignored.
    """
    # highway filters
    include_highway: Set[str] = field(default_factory=set)   # e.g. {"primary", "secondary"}
    exclude_highway: Set[str] = field(default_factory=set)   # e.g. {"service", "track"}

    # surface filters (e.g. {"asphalt", "concrete", "paved"})
    include_surface: Set[str] = field(default_factory=set)
    exclude_surface: Set[str] = field(default_factory=set)

    # access restriction (e.g. {"no", "private"})
    exclude_access: Set[str] = field(default_factory=set)

    # lanes (numeric)
    min_lanes: Optional[int] = None
    max_lanes: Optional[int] = None

    # oneway filter
    only_oneway: bool = False          # keep only oneway
    exclude_oneway: bool = False       # remove all oneway

    # length filter (in meters)
    min_length_m: Optional[float] = None
    max_length_m: Optional[float] = None

def _norm_str(val) -> Optional[str]:
    """
    Normalize a value to a lowercase string, or None if empty.
    
    Args:
        val: Input value to normalize (can be any type).
        
    Returns:
        Lowercase string representation of the value, or None if the value is empty.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return str(val)
    return str(val).strip().lower() if str(val).strip() else None

def _first_str(val) -> Optional[str]:
    """
    Handle OSM tag values that may be a list or scalar, returning the first normalized string.
    
    Args:
        val: OSM tag value that could be a single value, list, or tuple.
        
    Returns:
        Normalized string of the first value, or None if empty/invalid.
    """
    if val is None:
        return None
    if isinstance(val, (list, tuple)):
        return _norm_str(val[0]) if val else None
    return _norm_str(val)

def _parse_int(value) -> Optional[int]:
    """
    Parse an integer value from OSM data, handling semicolon-separated values.
    
    Args:
        value: Input value that may contain integer data (could be string with semicolons).
        
    Returns:
        Parsed integer value, or None if parsing fails. Takes the first value if semicolon-separated.
    """
    try:
        s = _first_str(value)
        if s is None:
            return None
        # handle "2;3"
        s = s.split(";")[0]
        return int(s)
    except Exception:
        return None

def _passes_string_set(val: Optional[str], include: Set[str], exclude: Set[str]) -> bool:
    """
    Check if a string value passes include/exclude filter criteria.
    
    Args:
        val: String value to check (normalized to lowercase).
        include: Set of allowed values (if empty, all values pass this criterion).
        exclude: Set of disallowed values.
        
    Returns:
        True if the value passes both include and exclude filters, False otherwise.
        If val is None and include is defined, returns False.
    """
    if val is None:
        # If include is defined, missing val should fail; else pass
        return len(include) == 0
    if include and val not in include:
        return False
    if exclude and val in exclude:
        return False
    return True

def _edge_length_m(geom: LineString) -> float:
    """
    Calculate the length of a LineString geometry in meters.
    
    Args:
        geom: LineString geometry (must be in a metric CRS).
        
    Returns:
        Length in meters, or 0.0 if calculation fails.
    """
    try:
        return float(geom.length)
    except Exception:
        return 0.0

def apply_filters(edges: Iterable[Edge], cfg: FilterConfig) -> List[Edge]:
    """
    Apply declarative filters to (geometry, attrs) edges.

    Args:
        edges: Iterable of (LineString_in_meters, attrs_dict). The geometry CRS must be metric.
        cfg: FilterConfig with include/exclude criteria.

    Returns:
        List[Edge]: Filtered edges.
    """
    # Pre-normalize sets to lowercase for faster lookups
    inc_hw = {s.lower() for s in (cfg.include_highway or set())}
    exc_hw = {s.lower() for s in (cfg.exclude_highway or set())}
    inc_surf = {s.lower() for s in (cfg.include_surface or set())}
    exc_surf = {s.lower() for s in (cfg.exclude_surface or set())}
    exc_acc = {s.lower() for s in (cfg.exclude_access or set())}

    out: List[Edge] = []
    for geom, attrs in edges:
        # Basic safe-guards
        if not isinstance(geom, LineString):
            continue
        length_m = _edge_length_m(geom)
        if cfg.min_length_m is not None and length_m < cfg.min_length_m:
            continue
        if cfg.max_length_m is not None and length_m > cfg.max_length_m:
            continue

        # Tags
        hw = _first_str(attrs.get("highway"))
        surf = _first_str(attrs.get("surface"))
        access = _first_str(attrs.get("access"))
        oneway = _first_str(attrs.get("oneway"))
        lanes = _parse_int(attrs.get("lanes"))

        # Highway include/exclude
        if not _passes_string_set(hw, inc_hw, exc_hw):
            continue

        # Surface include/exclude
        if not _passes_string_set(surf, inc_surf, exc_surf):
            continue

        # Access exclusions (e.g. no/private)
        if access in exc_acc:
            continue

        # Lanes range
        if cfg.min_lanes is not None and (lanes is None or lanes < cfg.min_lanes):
            continue
        if cfg.max_lanes is not None and (lanes is not None and lanes > cfg.max_lanes):
            continue

        # Oneway
        if cfg.only_oneway and oneway != "yes":
            continue
        if cfg.exclude_oneway and oneway == "yes":
            continue

        out.append((geom, attrs))
    return out
