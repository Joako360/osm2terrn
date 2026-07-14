"""Graph visualization helpers for local debugging."""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
from networkx import MultiDiGraph

from osm2terrn.utils.logger import get_logger

logger = get_logger("tools_visualization_graphs")


def plot_networkx_graph(
    graph: MultiDiGraph,
    title: str = "NetworkX Graph",
    node_size: int = 10,
    edge_color: str = "gray",
) -> None:
    """Render a graph using existing node x/y coordinates."""
    if graph is None or len(graph) == 0:
        logger.warning("Graph is empty. Nothing to plot.")
        return

    positions = {
        node: (data["x"], data["y"])
        for node, data in graph.nodes(data=True)
        if "x" in data and "y" in data
    }
    plt.figure(figsize=(12, 10))
    nx.draw(graph, positions, node_size=node_size, edge_color=edge_color, with_labels=False)
    plt.title(title)
    plt.show()
    logger.info(f"Plotted NetworkX graph: {title}.")
