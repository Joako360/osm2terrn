"""Heightmap and texture visualization helpers for local debugging."""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Colormap

from osm2terrn.utils.logger import get_logger

logger = get_logger("tools_visualization_heightmaps")

_PRESET_ALIASES = {
    "geo": "gist_earth",
    "cubehelix": "cubehelix",
    "bathymetry": "ocean",
    "earth": "terrain",
    "dem4": "terrain",
    "relief": "terrain",
    "bathy": "ocean",
}


def _resolve_colormap(cmap_name: Optional[str]) -> Colormap:
    requested = (cmap_name or "gist_earth").strip()
    candidate = _PRESET_ALIASES.get(requested.lower(), requested)
    try:
        return plt.get_cmap(candidate)
    except ValueError:
        logger.warning(f"Unknown colormap '{requested}'. Falling back to gist_earth.")
        return plt.get_cmap("gist_earth")


def _plot_2d_map(
    data: Any,
    title: str,
    cmap: Optional[Colormap | str],
    colorbar_label: Optional[str],
    xlabel: str,
    ylabel: str,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> None:
    if data is None:
        logger.warning(f"{title} is None. Nothing to plot.")
        return

    array = np.asarray(data)
    if array.size == 0:
        logger.warning(f"{title} is empty. Nothing to plot.")
        return

    if isinstance(cmap, str) or cmap is None:
        cmap = _resolve_colormap(cmap)

    plt.figure(figsize=(10, 8))
    image = plt.imshow(array, cmap=cmap, vmin=vmin, vmax=vmax)
    if colorbar_label:
        plt.colorbar(image, label=colorbar_label)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()
    logger.info(f"Plotted map: {title}.")


def plot_heightmap(
    heightmap: Any,
    title: str = "Heightmap",
    cmap_name: str = "terrain",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> None:
    """Render a heightmap matrix for development-time inspection."""
    _plot_2d_map(
        data=heightmap,
        title=title,
        cmap=cmap_name,
        colorbar_label="Elevation",
        xlabel="X",
        ylabel="Y",
        vmin=vmin,
        vmax=vmax,
    )


def plot_ground_texture(
    texture: Any,
    title: str = "Ground Texture",
    cmap_name: Optional[str] = None,
) -> None:
    """Render a generated texture matrix for development-time inspection."""
    _plot_2d_map(
        data=texture,
        title=title,
        cmap=cmap_name,
        colorbar_label=None,
        xlabel="X",
        ylabel="Y",
    )
