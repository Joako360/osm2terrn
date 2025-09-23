from typing import List, Dict
from math import atan2, degrees
from processing.road_model import Road

def to_procedural_roads_block(roads: List[Road]) -> str:
    """
    Generate a procedural roads block string for Terrn2 export.

    Args:
        roads (List[Road]): List of Road objects to export.

    Returns:
        str: Formatted procedural roads block as a string, suitable for inclusion in a .tobj file.
    """
    lines = ["begin_procedural_roads"]
    for r in roads:
        if r.name:
            lines.append(f"  // OSM street: {r.name}")
        if getattr(r, "is_bridge", False):
            lines.append("  // OSM: bridge=yes")
        lines.append("  road")
        lines.append(f"    width {r.width:.2f}")
        if r.border_width > 0:
            lines.append(f"    border_width {r.border_width:.2f}")
            lines.append(f"    border_height {r.border_height:.2f}")
        lines.append(f"    type {r.kind}")
        lines.append("    points")
        for x, z_planar, y_elev in r.points_m:
            # Write as X, Y(height), Z where Z is the planar Y component
            lines.append(f"      {x:.3f} {y_elev:.3f} {z_planar:.3f}")
        lines.append("    end_points")
        lines.append("  end_road")
    lines.append("end_procedural_roads")
    return "\n".join(lines)

def to_procedural_roads_blocks_per_segment(roads: List[Road]) -> str:
    """
    Generate one procedural roads block per Road segment.

    Each block is wrapped with begin_procedural_roads / end_procedural_roads
    and includes an optional OSM street comment when available.

    Float formatting follows project instructions.
    """
    blocks: List[str] = []
    for r in roads:
        lines = ["begin_procedural_roads"]
        if r.name:
            lines.append(f"  // OSM street: {r.name}")
        if getattr(r, "is_bridge", False):
            lines.append("  // OSM: bridge=yes")
        lines.append("  road")
        lines.append(f"    width {r.width:.2f}")
        if r.border_width > 0:
            lines.append(f"    border_width {r.border_width:.2f}")
            lines.append(f"    border_height {r.border_height:.2f}")
        lines.append(f"    type {r.kind}")
        lines.append("    points")
        for x, z_planar, y_elev in r.points_m:
            # Write as X, Y(height), Z where Z is the planar Y component
            lines.append(f"      {x:.3f} {y_elev:.3f} {z_planar:.3f}")
        lines.append("    end_points")
        lines.append("  end_road")
        lines.append("end_procedural_roads")
        blocks.append("\n".join(lines))
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
                "type": r.kind,
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

def map_osm_kind_to_ror(kind: str, fallback: str = "road") -> str:
    if not kind:
        return fallback
    return OSM_TO_ROR_OBJECT.get(kind, fallback)

def to_object_instance_lines(roads: List[Road], default_name: str = "road") -> List[str]:
    """
    Convert a list of Road polylines into .tobj object-instance lines.

    Each point becomes an instance line: "x, y, z, rx, ry, rz, name".
    - Coordinates are local meters (x, z). Y is elevation (set to 0.0 by default).
    - Rotation uses only the middle angle (ry) as heading (degrees) around up axis.
      The other angles (rx, rz) are set to 0.0.

    Float formatting follows project instructions:
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
        # Map OSM 'kind' to a RoR object label; fallback to provided default
        obj_name = map_osm_kind_to_ror(r.kind, default_name)
        if getattr(r, "is_bridge", False):
            obj_name = "roadbridge"
        # Optional street/way comment as a header for this segment
        if r.name:
            lines.append(f"// OSM street: {r.name}")
        if getattr(r, "is_bridge", False):
            lines.append("// OSM: bridge=yes")
        pts = r.points_m
        n = len(pts)
        for i, (x, z, y) in enumerate(pts):
            # Determine heading from neighbor points in XZ plane
            if i < n - 1:
                nx, nz, _ = pts[i + 1]
                dx, dz = (nx - x), (nz - z)
            elif i > 0:
                px, pz, _ = pts[i - 1]
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
                f"{x:.3f}, {y_val:.6f}, {z:.3f}, "
                f"{rx:.6f}, {ry:.6f}, {rz:.6f}, {obj_name}"
            )
            lines.append(line)
    return lines
