"""OSM2terrn data processing package."""

from __future__ import annotations

__all__ = [
    "download_data_from_bbox",
    "download_menu",
    "download_builings_from_overture",
    "DownloadMenu",
]


def __getattr__(name: str):
    """Lazily expose data helpers without importing the CLI during package initialization."""
    if name == "DownloadMenu":
        from .download_menu import DownloadMenu

        return DownloadMenu

    if name in {"download_data_from_bbox", "download_menu", "download_builings_from_overture"}:
        from .osm_data_handler import (
            download_builings_from_overture,
            download_data_from_bbox,
            download_menu,
        )

        return {
            "download_data_from_bbox": download_data_from_bbox,
            "download_menu": download_menu,
            "download_builings_from_overture": download_builings_from_overture,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")