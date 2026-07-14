from __future__ import annotations

import hashlib

import geopandas as gpd

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.entities import Road
from osm2terrn.domain.value_objects import Point2D, Polyline


_DOMAIN_ROADS_CACHE_NAMESPACE = "domain/adapters/roads"
_DOMAIN_ROADS_ALGORITHM_VERSION = "1"


def fingerprint_geodataframe(gdf: gpd.GeoDataFrame) -> dict[str, object]:
    """Return a deterministic fingerprint payload for a GeoDataFrame."""

    geometry_hasher = hashlib.sha256()
    for index, geometry in zip(gdf.index.tolist(), gdf.geometry):
        geometry_hasher.update(str(index).encode("utf-8"))
        if geometry is None:
            geometry_hasher.update(b"<none>")
        else:
            geometry_hasher.update(bytes(geometry.wkb))

    name_hasher = hashlib.sha256()
    if "name" in gdf.columns:
        for value in gdf["name"].tolist():
            name_hasher.update(repr(value).encode("utf-8"))

    bounds = [float(v) for v in gdf.total_bounds] if len(gdf) > 0 else [0.0, 0.0, 0.0, 0.0]
    return {
        "rows": int(len(gdf)),
        "columns": [str(col) for col in gdf.columns.tolist()],
        "crs": str(gdf.crs) if gdf.crs is not None else None,
        "bounds": bounds,
        "geometry_hash": geometry_hasher.hexdigest(),
        "name_hash": name_hasher.hexdigest(),
    }


def geodataframe_to_roads(gdf: gpd.GeoDataFrame) -> list[Road]:
    """Convert a GeoDataFrame into domain-level road entities.

    This adapter isolates OSMnx/GeoPandas-specific details from the domain layer.
    """

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[list[Road]]()
    cache_key = cache_manager.build_key(
        {
            "gdf": fingerprint_geodataframe(gdf),
        },
        provider="domain_adapter",
        algorithm_version=_DOMAIN_ROADS_ALGORITHM_VERSION,
        format_version="1",
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
            continue
        if hasattr(geometry, "geoms"):
            coords = [Point2D(float(x), float(y)) for x, y in geometry.geoms[0].coords]
        else:
            coords = [Point2D(float(x), float(y)) for x, y in geometry.coords]
        road = Road(
            id=str(index),
            geometry=Polyline(tuple(coords)),
            metadata={"source": "osmnx", "name": row.get("name")},
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
            format_version="1",
            extra={"road_count": int(len(roads))},
        ),
    )
    return roads
