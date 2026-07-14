from typing import List
from osm2terrn.processing.roads.road_geometry import compute_heading_pitch
from osm2terrn.processing.roads.road_model import Road
from osm2terrn.utils.logger import get_logger, log_info

logger = get_logger("road_exporters_blocks")


def export_procedural_roads_block(roads: List[Road], per_segment: bool = False) -> str:
    if not roads:
        log_info(logger, "No roads to export")
        return ""
    return _export_roads_per_segment(roads) if per_segment else _export_roads_single_block(roads)


def _export_roads_single_block(roads: List[Road]) -> str:
    blocks = []
    for road in roads:
        lines = []
        if hasattr(road, 'name') and road.name:
            lines.append(f"// OSM street: {road.name}")
        if getattr(road, "is_bridge", False):
            lines.append("// OSM: bridge=yes")
        lines.append("begin_procedural_roads")
        for index, point in enumerate(road.points_m):
            x, y, z = point[0], point[1], point[2] if len(point) > 2 else 0.0
            rot_x = road.pitch_deg[index] if road.pitch_deg is not None and index < len(road.pitch_deg) else 0.0
            rot_y = road.yaw_deg[index] if road.yaw_deg is not None and index < len(road.yaw_deg) else 0.0
            rot_z = road.roll_deg[index] if road.roll_deg is not None and index < len(road.roll_deg) else 0.0
            road_type = road.type if road.type else "flat"
            lines.append(
                f" {x:.3f}, {y:.3f}, {z:.3f}, "
                f"{rot_y:.6f}, {rot_x:.6f}, {rot_z:.6f}, "
                f"{road.width:.2f}, {road.border_width:.2f}, {road.border_height:.2f}, "
                f"{road_type}"
            )
        lines.append("end_procedural_roads")
        blocks.append("\n".join(lines))
    log_info(logger, f"✅ Generated {len(blocks)} procedural roads blocks")
    return "\n\n".join(blocks)


def _export_roads_per_segment(roads: List[Road]) -> str:
    blocks = []
    for road in roads:
        lines = []
        if hasattr(road, 'name') and road.name:
            lines.append(f"// OSM street: {road.name}")
        if getattr(road, "is_bridge", False):
            lines.append("// OSM: bridge=yes")
        lines.append("begin_procedural_roads")
        for index, point in enumerate(road.points_m):
            x, y, z = point[0], point[1], point[2] if len(point) > 2 else 0.0
            rot_x = road.pitch_deg[index] if road.pitch_deg is not None and index < len(road.pitch_deg) else 0.0
            rot_y = road.yaw_deg[index] if road.yaw_deg is not None and index < len(road.yaw_deg) else 0.0
            rot_z = road.roll_deg[index] if road.roll_deg is not None and index < len(road.roll_deg) else 0.0
            road_type = road.type if road.type else "flat"
            lines.append(
                f" {x:.3f}, {y:.3f}, {z:.3f}, "
                f"{rot_y:.6f}, {rot_x:.6f}, {rot_z:.6f}, "
                f"{road.width:.2f}, {road.border_width:.2f}, {road.border_height:.2f}, "
                f"{road_type}"
            )
        lines.append("end_road")
        lines.append("end_procedural_roads")
        blocks.append("\n".join(lines))
    log_info(logger, f"✅ Generated {len(blocks)} separate procedural roads blocks")
    return "\n\n".join(blocks)
