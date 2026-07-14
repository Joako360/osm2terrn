from typing import Dict, List
from osm2terrn.processing.roads.road_geometry import compute_heading_pitch
from osm2terrn.processing.roads.road_model import Road

OSM_TO_ROR_OBJECT = {
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


def to_intermediate_json(roads: List[Road]) -> Dict:
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


def to_object_instance_lines(roads: List[Road], default_name: str = "road") -> List[str]:
    lines: List[str] = []
    for r in roads:
        obj_name = map_osm_type_to_ror(r.type, default_name)
        if getattr(r, "is_bridge", False):
            obj_name = "roadbridge"
        if r.name:
            lines.append(f"// OSM street: {r.name}")
        if getattr(r, "is_bridge", False):
            lines.append("// OSM: bridge=yes")
        pts = r.points_m
        n = len(pts)
        for i, (x, y, z) in enumerate(pts):
            if i < n - 1:
                nx, ny, nz = pts[i + 1]
                dx, dz = (nx - x), (nz - z)
            elif i > 0:
                px, py, pz = pts[i - 1]
                dx, dz = (x - px), (z - pz)
            else:
                dx, dz = 1.0, 0.0
            heading_deg, _ = compute_heading_pitch(dx, dz)
            rx = 0.0
            ry = heading_deg
            rz = 0.0
            y_val = float(y) if y is not None else 0.0
            lines.append(
                f"{x:.3f}, {y_val:.3f}, {z:.3f}, "
                f"{rx:.6f}, {ry:.6f}, {rz:.6f}, {obj_name}"
            )
    return lines
