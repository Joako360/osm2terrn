"""GeoDataFrame visualization helpers for local debugging."""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
from geopandas import GeoDataFrame

from osm2terrn.utils.logger import get_logger

logger = get_logger("tools_visualization_geodata")


def plot_geodataframe(gdf: GeoDataFrame, title: str = "GeoDataFrame", ax: Optional[Any] = None) -> None:
    """Render a GeoDataFrame with matplotlib for interactive inspection."""
    if gdf is None or gdf.empty:
        logger.warning("GeoDataFrame is empty. Nothing to plot.")
        return

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(ax=ax)
    ax.set_title(title)
    plt.show()
    logger.info(f"Plotted GeoDataFrame: {title}.")
