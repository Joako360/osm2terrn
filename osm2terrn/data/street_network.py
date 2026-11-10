"""Explicit acquisition state for the canonical OSM street graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import networkx as nx
from pyproj import CRS


StreetAcquisitionStatus = Literal[
    "not_requested",
    "missing",
    "available",
    "empty",
    "failed",
]
StreetAcquisitionSource = Literal["none", "query", "cache", "cache_recovered"]


@dataclass(slots=True)
class StreetNetworkResult:
    """Describe acquisition of streets while retaining the graph as source of truth.

    ``graph_crs`` is a normalized declaration that must agree with the graph's
    ``graph['crs']`` metadata. The graph is never copied or altered by this
    result object.
    """

    status: StreetAcquisitionStatus
    graph: nx.MultiDiGraph | None = None
    graph_crs: str | None = None
    diagnostic: str | None = None
    source: StreetAcquisitionSource = "query"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Raise when result fields do not match the acquisition status."""

        if self.status not in {"not_requested", "missing", "available", "empty", "failed"}:
            raise ValueError(f"Unknown street acquisition status: {self.status!r}")
        if self.source not in {"none", "query", "cache", "cache_recovered"}:
            raise ValueError(f"Unknown street acquisition source: {self.source!r}")
        if self.status in {"available", "empty"} and self.graph is not None:
            if self.status == "available" and self.graph.number_of_edges() == 0:
                raise ValueError("Available street result requires a graph with edges")
            if self.status == "empty":
                if self.graph.number_of_edges() != 0:
                    raise ValueError("Empty street result cannot carry a graph with edges")
                if len(self.graph.nodes) == 0:
                    raise ValueError("Empty street result must use graph=None when there are no nodes")
            graph_crs = self.graph.graph.get("crs")
            if graph_crs is None or self.graph_crs is None:
                raise ValueError(f"{self.status.capitalize()} street result with a graph requires an explicit graph CRS")
            declared_crs = CRS.from_user_input(self.graph_crs)
            actual_crs = CRS.from_user_input(graph_crs)
            if declared_crs != actual_crs:
                raise ValueError("Street result CRS does not match graph metadata")
            return
        if self.status == "available":
            raise ValueError("Available street result requires a graph with edges")

        if self.graph is not None or self.graph_crs is not None:
            raise ValueError(f"Street result status {self.status!r} cannot carry a graph or CRS")
        if self.status == "failed" and not (self.diagnostic and self.diagnostic.strip()):
            raise ValueError("Failed street result requires a diagnostic")

