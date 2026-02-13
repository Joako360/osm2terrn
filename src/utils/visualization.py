import matplotlib.pyplot as plt
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
import networkx as nx
from typing import Optional, Any
from utils.logger import get_logger

logger = get_logger("visualization")


def plot_geodataframe(gdf: GeoDataFrame, title: str = "GeoDataFrame", ax: Optional[Any] = None) -> None:
    """
    Plot a GeoDataFrame using matplotlib.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame to plot.
        title (str): Title for the plot.
        ax (matplotlib.axes.Axes, optional): Existing matplotlib axes to plot on.

    Returns:
        None
    """
    if gdf is None or gdf.empty:
        logger.warning("GeoDataFrame is empty. Nothing to plot.")
        return

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(ax=ax)
    ax.set_title(title)
    plt.show()
    logger.info(f"Plotted GeoDataFrame: {title}.")


def plot_networkx_graph(G: MultiDiGraph, title: str = "NetworkX Graph", node_size: int = 10, edge_color: str = "gray") -> None:
    """
    Plot a NetworkX MultiDiGraph using matplotlib.

    Args:
        G (MultiDiGraph): The graph to plot.
        title (str): Title for the plot.
        node_size (int): Size of the nodes.
        edge_color (str): Color of the edges.

    Returns:
        None
    """
    if G is None or len(G) == 0:
        logger.warning("Graph is empty. Nothing to plot.")
        return

    pos = {n: (data["x"], data["y"]) for n, data in G.nodes(data=True) if "x" in data and "y" in data}
    plt.figure(figsize=(12, 10))
    nx.draw(G, pos, node_size=node_size, edge_color=edge_color, with_labels=False)
    plt.title(title)
    plt.show()
    logger.info(f"Plotted NetworkX graph: {title}.")


def plot_heightmap(heightmap, title: str = "Heightmap") -> None:
    """
    Plot a heightmap (2D numpy array) using matplotlib.

    Args:
        heightmap (np.ndarray): The heightmap array to plot.
        title (str): Title for the plot.

    Returns:
        None
    """
    if heightmap is None:
        logger.warning("Heightmap is None. Nothing to plot.")
        return

    plt.figure(figsize=(10, 8))
    plt.imshow(heightmap, cmap="terrain")
    plt.colorbar(label="Elevation")
    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()