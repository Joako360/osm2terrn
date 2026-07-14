from typing import Any

from osm2terrn.config.settings import get_program_config


class MapData:
    """Holds the downloaded map data and related session metadata."""

    def __init__(self) -> None:
        config = get_program_config()
        self.data: dict[str, Any] = {}
        self.elevation_data: dict[str, Any] = {}
        self.place: str = config.terrain_runtime.default_place_name
        self.origin_lon: float = 0.0
        self.origin_lat: float = 0.0

    def has_data(self) -> bool:
        return bool(self.data)


current_map = MapData()
