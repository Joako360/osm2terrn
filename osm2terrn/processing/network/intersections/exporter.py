"""Exporter helpers to emit Rigs of Rods placement lines (.tobj style).

Provide a minimal helper that formats a prefab placement line. The
exporter in the project can consume these strings when writing the final
.tobj file.
"""
from typing import Tuple


def export_prefab_tobj(object_name: str, position: Tuple[float, float, float], rotation_yaw: float) -> str:
    """Return a single-line TOBJ placement record for a prefab.

    The format used here is a compact CSV-like line that the project's
    existing exporter can parse. Adjust as needed to match exact exporter.
    """
    x, y, z = position
    # yaw in degrees
    return f"{object_name}, {x:.3f}, {y:.3f}, {z:.3f}, 0, {rotation_yaw:.1f}, 0"
