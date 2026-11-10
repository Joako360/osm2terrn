from __future__ import annotations

import hashlib
from typing import Any

import geopandas as gpd
import networkx as nx
from pyproj import CRS
from shapely.geometry import LineString

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.entities import Road
from osm2terrn.domain.value_objects import Point2D, Polyline


_DOMAIN_ROADS_CACHE_NAMESPACE = "domain/adapters/roads"
_DOMAIN_ROADS_ALGORITHM_VERSION = "2"


def fingerprint_geodataframe(gdf: gpd.GeoDataFrame) -> dict[str, object]:
    """Return a deterministic fingerprint payload for a GeoDataFrame."""

    geometry_hasher = hashlib.sha256()
    for index, geometry in zip(gdf.index.tolist(), gdf.geometry):
        geometry_hasher.update(str(index).encode("utf-8"))
        if geometry is None:
            geometry_hasher.update(b"<none>")
        else:
            geometry_hasher.update(bytes(geometry.wkb))

    attributes_hasher = hashlib.sha256()
    attribute_columns = [column for column in gdf.columns if column != gdf.geometry.name]
    attribute_values = [gdf[column].tolist() for column in attribute_columns]
    for index, values in zip(gdf.index.tolist(), zip(*attribute_values)):
        attributes_hasher.update(
            repr((index, tuple((column, repr(value)) for column, value in zip(attribute_columns, values)))).encode(
                "utf-8"
            )
        )

    bounds = [float(v) for v in gdf.total_bounds] if len(gdf) > 0 else [0.0, 0.0, 0.0, 0.0]
    return {
        "rows": int(len(gdf)),
        "columns": [str(col) for col in gdf.columns.tolist()],
        "crs": str(gdf.crs) if gdf.crs is not None else None,
        "bounds": bounds,
        "geometry_hash": geometry_hasher.hexdigest(),
        "attributes_hash": attributes_hasher.hexdigest(),
    }


def graph_to_roads_geodataframe(
    graph: nx.MultiDiGraph,
    *,
    target_crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """Convert graph edges to a GeoDataFrame in an explicit target CRS.

    The graph is treated as canonical and is never modified. Edge attributes
    and keys are retained as columns. Missing edge geometry is represented by
    a line between its graph nodes in the graph's declared CRS.
    """

    source_crs_value = graph.graph.get("crs")
    if source_crs_value is None:
        raise ValueError("Street graph must declare graph['crs'] before conversion")
    source_crs = CRS.from_user_input(source_crs_value)
    target = CRS.from_user_input(target_crs)

    rows: list[dict[str, Any]] = []
    for u, v, key, attributes in graph.edges(keys=True, data=True):
        geometry = attributes.get("geometry")
        if geometry is None:
            try:
                start = graph.nodes[u]
                end = graph.nodes[v]
                geometry = LineString(((float(start["x"]), float(start["y"])), (float(end["x"]), float(end["y"]))))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Street edge {(u, v, key)!r} has no usable geometry or endpoint coordinates") from exc
        row = dict(attributes)
        row.update({"u": u, "v": v, "key": key, "geometry": geometry})
        row["edge_id"] = f"edge:{u!r}:{v!r}:{key!r}"
        rows.append(row)

    if rows:
        source_gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=source_crs)
    else:
        source_gdf = gpd.GeoDataFrame(
            {"edge_id": [], "u": [], "v": [], "key": [], "geometry": []},
            geometry="geometry",
            crs=source_crs,
        )
    try:
        return source_gdf.to_crs(target)
    except Exception as exc:
        raise ValueError(f"Could not transform street geometries from {source_crs} to {target}") from exc


def geodataframe_to_roads(gdf: gpd.GeoDataFrame) -> list[Road]:
    """Convert a GeoDataFrame into domain-level road entities.

    This adapter isolates OSMnx/GeoPandas-specific details from the domain layer.
    Coordinates must be EPSG:4326; feature attributes are retained in metadata.
    """

    if gdf.crs is None or CRS.from_user_input(gdf.crs) != CRS.from_epsg(4326):
        raise ValueError("Road GeoDataFrame must use EPSG:4326 coordinates")

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[list[Road]]()
    cache_key = cache_manager.build_key(
        {
            "gdf": fingerprint_geodataframe(gdf),
        },
        provider="domain_adapter",
        algorithm_version=_DOMAIN_ROADS_ALGORITHM_VERSION,
        format_version="2",
        artifact_type="domain_roads",
    )
    cached = cache_manager.get(
        namespace=_DOMAIN_ROADS_CACHE_NAMESPACE,
        key=cache_key,
        serializer=serializer,
    )
    if cached is not None:
        return cached[0]

    roads: list[Road] = []
    for index, row in gdf.iterrows():
        geometry = row.geometry
        if geometry is None:
            raise ValueError(f"Road geometry at index {index!r} is missing")
        parts = list(geometry.geoms) if geometry.geom_type == "MultiLineString" else [geometry]
        for part_index, part in enumerate(parts):
            if part.geom_type != "LineString" or len(part.coords) < 2:
                raise ValueError(f"Road geometry at index {index!r} is not a usable line")
            coords = [Point2D(float(x), float(y)) for x, y, *_ in part.coords]
            attributes = {
                str(column): _plain_value(row[column])
                for column in gdf.columns
                if column != gdf.geometry.name
            }
            road_id = str(row.get("edge_id", index))
            if len(parts) > 1:
                road_id = f"{road_id}:part:{part_index}"
            road = Road(
                id=road_id,
                geometry=Polyline(tuple(coords)),
                surface=_plain_value(row.get("highway")),
                metadata={"source": "osmnx", "name": _plain_value(row.get("name")), "osm_attributes": attributes},
            )
            roads.append(road)

    cache_manager.put(
        namespace=_DOMAIN_ROADS_CACHE_NAMESPACE,
        key=cache_key,
        value=roads,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="domain_roads",
            provider="domain_adapter",
            algorithm_version=_DOMAIN_ROADS_ALGORITHM_VERSION,
            format_version="2",
            extra={"road_count": int(len(roads))},
        ),
    )
    return roads


def _plain_value(value: Any) -> Any:
    """Convert common NumPy scalar values without discarding attributes."""

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    return value
