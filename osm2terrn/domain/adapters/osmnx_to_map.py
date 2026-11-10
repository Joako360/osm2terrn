from __future__ import annotations

from typing import Any

import geopandas as gpd
from pyproj import CRS

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.adapters.bounds import to_domain_bounding_box
from osm2terrn.domain.adapters.osmnx_to_buildings import geodataframe_to_buildings
from osm2terrn.domain.adapters.osmnx_to_roads import (
    fingerprint_geodataframe,
    geodataframe_to_roads,
)
from osm2terrn.domain.entities import MapData
from osm2terrn.domain.value_objects import BoundingBox


_MAPDATA_CACHE_NAMESPACE = "domain/adapters/mapdata"
_MAPDATA_ALGORITHM_VERSION = "3"


def geodataframe_to_mapdata(gdf: gpd.GeoDataFrame) -> MapData:
    """Create a minimal MapData aggregate from a GeoDataFrame-like input."""
    cache_manager = get_cache_manager()
    serializer = PickleSerializer[MapData]()
    cache_key = cache_manager.build_key(
        {"gdf": fingerprint_geodataframe(gdf)},
        provider="domain_adapter",
        algorithm_version=_MAPDATA_ALGORITHM_VERSION,
        format_version="3",
        artifact_type="mapdata",
    )
    cached = cache_manager.get(namespace=_MAPDATA_CACHE_NAMESPACE, key=cache_key, serializer=serializer)
    if cached is not None:
        return cached[0]

    map_data = MapData(roads=geodataframe_to_roads(gdf), coordinate_system="EPSG:4326")
    cache_manager.put(
        namespace=_MAPDATA_CACHE_NAMESPACE,
        key=cache_key,
        value=map_data,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="mapdata",
            provider="domain_adapter",
            algorithm_version=_MAPDATA_ALGORITHM_VERSION,
            format_version="3",
            extra={"road_count": int(len(map_data.roads))},
        ),
    )
    return map_data


def build_mapdata_from_pipeline_context(
    *,
    bounds: BoundingBox | gpd.GeoDataFrame | None = None,
    place: str | None = None,
    roads_gdf: gpd.GeoDataFrame | None = None,
    buildings_gdf: gpd.GeoDataFrame | None = None,
    metadata: dict[str, Any] | None = None,
) -> MapData:
    """Build domain MapData from pipeline inputs.

    Road and building GeoDataFrames must use EPSG:4326 coordinates.
    """
    bounding_box = to_domain_bounding_box(bounds) if bounds is not None else None
    if bounds is not None and bounding_box is None:
        raise ValueError("bounds must be convertible to a domain BoundingBox")

    for data_name, geodataframe in (("roads_gdf", roads_gdf), ("buildings_gdf", buildings_gdf)):
        if geodataframe is not None and (
            geodataframe.crs is None or CRS.from_user_input(geodataframe.crs) != CRS.from_epsg(4326)
        ):
            raise ValueError(f"{data_name} must use EPSG:4326 coordinates before building MapData")

    cache_inputs = {
        "bounds": (
            {
                "bounds": [float(value) for value in bounding_box.to_tuple()],
                "crs": bounding_box.crs,
                "is_projected": bool(bounding_box.is_projected),
            }
            if bounding_box is not None
            else None
        ),
        "place": place or "",
        "roads_gdf": fingerprint_geodataframe(roads_gdf) if roads_gdf is not None else None,
        "buildings_gdf": fingerprint_geodataframe(buildings_gdf) if buildings_gdf is not None else None,
        "metadata": metadata or {},
    }

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[MapData]()
    cache_key = cache_manager.build_key(
        cache_inputs,
        provider="domain_adapter",
        algorithm_version=_MAPDATA_ALGORITHM_VERSION,
        format_version="3",
        artifact_type="mapdata",
    )
    cached = cache_manager.get(namespace=_MAPDATA_CACHE_NAMESPACE, key=cache_key, serializer=serializer)
    if cached is not None:
        return cached[0]

    roads = geodataframe_to_roads(roads_gdf) if roads_gdf is not None else []
    buildings = geodataframe_to_buildings(buildings_gdf) if buildings_gdf is not None else []
    map_data = MapData(
        roads=roads,
        buildings=buildings,
        bounding_box=bounding_box,
        coordinate_system="EPSG:4326",
        metadata={
            "place": place or "",
            "source": "pipeline",
            **(metadata or {}),
        },
    )
    cache_manager.put(
        namespace=_MAPDATA_CACHE_NAMESPACE,
        key=cache_key,
        value=map_data,
        serializer=serializer,
        metadata=CacheMetadata(
            artifact_type="mapdata",
            provider="domain_adapter",
            algorithm_version=_MAPDATA_ALGORITHM_VERSION,
            format_version="3",
            extra={
                "road_count": int(len(map_data.roads)),
                "building_count": int(len(map_data.buildings)),
            },
        ),
    )
    return map_data
