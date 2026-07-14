"""Intersection detector helpers

Provide small, dependency-light helpers to detect candidate intersection
nodes from a road adjacency representation.

We intentionally avoid heavy GIS deps here; the functions accept plain
Python structures (adjacency dicts, coordinate maps) to keep testing
simple and integration flexible.
"""
from typing import Dict, Iterable, List, Tuple

Adjacency = Dict[str, List[str]]
CoordMap = Dict[str, Tuple[float, float]]


def detect_intersection_nodes(adjacency: Adjacency) -> List[str]:
    """Return list of node ids which are candidate intersections.

    A simple rule: degree != 2. Caller must provide a cleaned adjacency
    where minor service nodes may already be filtered.
    """
    return [node for node, neighbors in adjacency.items() if len(neighbors) != 2]


def build_adjacency_from_edges(edges: Iterable[Tuple[str, str]]) -> Adjacency:
    """Build adjacency dict from an iterable of (u, v) edges.

    Nodes are represented as hashable ids (strings or ints converted
    to str). Useful for tests and lightweight graph handling.
    """
    adj: Adjacency = {}
    for u, v in edges:
        u_s, v_s = str(u), str(v)
        adj.setdefault(u_s, []).append(v_s)
        adj.setdefault(v_s, []).append(u_s)
    return adj
