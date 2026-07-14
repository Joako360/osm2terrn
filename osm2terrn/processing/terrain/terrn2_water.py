from typing import Dict, Optional
import uuid

from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_info, log_error

logger = get_logger("terrn2_water")
_PROGRAM_CONFIG = get_program_config()


def _generate_guid() -> str:
    return str(uuid.uuid4())


def prepare_water_config(
    elevation_stats: Optional[Dict[str, float]] = None,
    water_config: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    if _PROGRAM_CONFIG.water_runtime.enable_realistic_water and elevation_stats:
        try:
            min_elev = elevation_stats.get('min_elevation', 0.0)
            max_elev = elevation_stats.get('max_elevation', 100.0)
            water_level = min_elev
            water_bottom = water_level - _PROGRAM_CONFIG.water_runtime.default_water_depth
            config = {
                "enabled": True,
                "water_line": water_level,
                "water_bottom_line": water_bottom,
            }
            log_info(logger, f"Prepared realistic water config: {config}")
            return config
        except Exception as e:
            log_error(logger, f"Error preparing realistic water config: {e}")

    if water_config:
        return water_config

    return {
        "enabled": bool(_PROGRAM_CONFIG.water_runtime.default_water_enabled),
        "water_line": _PROGRAM_CONFIG.water_runtime.default_water_line,
        "water_bottom_line": _PROGRAM_CONFIG.water_runtime.default_water_bottom_line,
    }
