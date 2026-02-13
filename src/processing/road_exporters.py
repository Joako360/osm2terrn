from typing import List, Dict
from math import atan2, degrees
from processing.road_model import Road
from utils.logger import get_logger, log_info

logger = get_logger("road_exporters")

def export_procedural_roads_block(roads: List[Road], per_segment: bool = False) -> str:
    """
    Generate a complete procedural roads block for Terrn2 export.

    Terrn2 supports and generally prefers procedural roads sections over placing
    roads as object instances. This function is the single source of truth for
    procedural roads formatting and consolidates all road export logic.

    Args:
        roads (List[Road]): List of Road objects to export.
        per_segment (bool): If True, create one block per road segment.
                           If False, create a single block with all roads.

    Returns:
        str: Formatted procedural roads block(s) ready for .tobj file.
    """
    if not roads:
        log_info(logger, "No roads to export")
        return ""

    if per_segment:
        return _export_roads_per_segment(roads)
    else:
        return _export_roads_single_block(roads)


def _export_roads_single_block(roads: List[Road]) -> str:
    """
    Generate separate procedural roads blocks, one per road.

    Args:
        roads (List[Road]): List of Road objects.

    Returns:
        str: Complete procedural roads blocks as string.
    """
    blocks = []
    
    for road in roads:
        lines = ["begin_procedural_roads"]
        
        # Add metadata comments
        if hasattr(road, 'name') and road.name:
            lines.append(f"  // OSM street: {road.name}")
        if getattr(road, "is_bridge", False):
            lines.append("  // OSM: bridge=yes")
        
        # Points - each point on its own line with all required values
        for point in road.points_m:
            x, y, z = point[0], point[1], point[2] if len(point) > 2 else 0.0
            yaw, pitch, roll = 0.0, 0.0, 0.0
            # Format: x, y, z, yaw, pitch, roll, width, border_width, border_height, flags, material, smoothness, type
            lines.append(
                f"  {x:.6f}, {y:.6f}, {z:.6f}, "
                f"{yaw:.6f}, {pitch:.6f}, {roll:.6f}, "
                f"{road.width:.2f}, {road.border_width:.2f}, {road.border_height:.2f}, "
                f"1, 0, 0, {road.type}"
            )
        
        lines.append("end_procedural_roads")
        blocks.append("\n".join(lines))
    
    log_info(logger, f"✅ Generated {len(blocks)} procedural roads blocks")
    return "\n\n".join(blocks)


def _export_roads_per_segment(roads: List[Road]) -> str:
    """
    Generate one procedural roads block per road segment.

    Args:
        roads (List[Road]): List of Road objects.

    Returns:
        str: Multiple procedural roads blocks, one per road.
    """
    blocks = []
    
    for road in roads:
        lines = ["begin_procedural_roads"]
        
        if hasattr(road, 'name') and road.name:
            lines.append(f"  // OSM street: {road.name}")
        if getattr(road, "is_bridge", False):
            lines.append("  // OSM: bridge=yes")
        
        lines.append("  road")
        lines.append(f"    width {road.width:.2f}")
        
        if road.border_width > 0:
            lines.append(f"    border_width {road.border_width:.2f}")
            lines.append(f"    border_height {road.border_height:.2f}")
        
        lines.append(f"    type {road.type}")
        lines.append("    points")
        
        for x, y_elev, z_planar in road.points_m:
            lines.append(f"      {x:.3f} {y_elev:.3f} {z_planar:.3f}")
        
        lines.append("    end_points")
        lines.append("  end_road")
        lines.append("end_procedural_roads")
        
        blocks.append("\n".join(lines))
    
    log_info(logger, f"✅ Generated {len(blocks)} separate procedural roads blocks")
    return "\n".join(blocks)

def to_intermediate_json(roads: List[Road]) -> Dict:
    """
    Convert a list of Road objects to an intermediate JSON-serializable dictionary.

    Args:
        roads (List[Road]): List of Road objects to serialize.

    Returns:
        Dict: Dictionary containing road data for debugging or inspection.
    """
    return {
        "roads": [
            {
                "width": r.width,
                "border_width": r.border_width,
                "border_height": r.border_height,
                "type": r.type,
                "points_m": r.points_m,
            }
            for r in roads
        ]
    }

OSM_TO_ROR_OBJECT = {
    # Simplified mapping; extend as needed
    "motorway": "road",
    "trunk": "road",
    "primary": "road",
    "secondary": "road",
    "tertiary": "road",
    "residential": "road-both",
    "living_street": "road-both",
    "service": "road-park",
    "footway": "road",
    "path": "road",
    "track": "road",
}

def map_osm_type_to_ror(type: str, fallback: str = "road") -> str:
    if not type:
        return fallback
    return OSM_TO_ROR_OBJECT.get(type, fallback)

def to_object_instance_lines(roads: List[Road], default_name: str = "road") -> List[str]:
    """
    Convert a list of Road polylines into .tobj object-instance lines.

    Note: Terrn2 generally prefers the procedural roads section for roads.
    This function remains available as an alternative/fallback that places each
    road polyline vertex as an object instance (legacy approach).

    Each point becomes an instance line: "x, y, z, rx, ry, rz, name".
    - Coordinates are local meters (x, z). Y is elevation (set to 0.0 by default).
    - Rotation uses only the middle angle (ry) as heading (degrees) around up axis.
      The other angles (rx, rz) are set to 0.0.

    Float formatting:
    - Coordinates: "{:.3f}"
    - Rotations: "{:.6f}"

    Args:
        roads: List of Road objects.
        default_name: Object type/name to use when Road.kind is empty.

    Returns:
        List[str]: Lines ready to be written into a .tobj file.
    """
    lines: List[str] = []
    for r in roads:
        # Map OSM 'type' to a RoR object label; fallback to provided default
        obj_name = map_osm_type_to_ror(r.type, default_name)
        if getattr(r, "is_bridge", False):
            obj_name = "roadbridge"
        # Optional street/way comment as a header for this segment
        if r.name:
            lines.append(f"// OSM street: {r.name}")
        if getattr(r, "is_bridge", False):
            lines.append("// OSM: bridge=yes")
        pts = r.points_m
        n = len(pts)
        for i, (x, y, z) in enumerate(pts):
            # Determine heading from neighbor points in XZ plane
            if i < n - 1:
                nx, ny, nz = pts[i + 1]
                dx, dz = (nx - x), (nz - z)
            elif i > 0:
                px, py, pz = pts[i - 1]
                dx, dz = (x - px), (z - pz)
            else:
                dx, dz = 1.0, 0.0  # Fallback heading along +X
            # yaw around up-axis; examples show second angle carries heading
            heading_deg = degrees(atan2(dz, dx))
            rx = 0.0
            ry = heading_deg
            rz = 0.0
            # Use provided elevation if available; default to 0.0
            y_val = float(y) if y is not None else 0.0
            line = (
                f"{x:.3f}, {y_val:.3f}, {z:.3f}, "
                f"{rx:.6f}, {ry:.6f}, {rz:.6f}, {obj_name}"
            )
            lines.append(line)
    return lines
#loadscript road_editor.as