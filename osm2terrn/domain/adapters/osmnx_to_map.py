from __future__ import annotations

from typing import Any

import geopandas as gpd

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.domain.adapters.osmnx_to_roads import geodataframe_to_roads
from osm2terrn.domain.adapters.osmnx_to_roads import fingerprint_geodataframe
from osm2terrn.domain.entities import MapData
from osm2terrn.domain.value_objects import BoundingBox


_MAPDATA_CACHE_NAMESPACE = "domain/adapters/mapdata"
_MAPDATA_ALGORITHM_VERSION = "1"


def geodataframe_to_mapdata(gdf: object) -> MapData:
    """Create a minimal MapData aggregate from a GeoDataFrame-like input."""
    cache_manager = get_cache_manager()
    serializer = PickleSerializer[MapData]()
    cache_key = cache_manager.build_key(
        {
            "gdf": fingerprint_geodataframe(gdf),
        },
        provider="domain_adapter",
        algorithm_version=_MAPDATA_ALGORITHM_VERSION,
        format_version="1",
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
            format_version="1",
            extra={"road_count": int(len(map_data.roads))},
        ),
    )
    return map_data


def build_mapdata_from_pipeline_context(
    *,
    bounds: gpd.GeoDataFrame | None = None,
    place: str | None = None,
    roads_gdf: gpd.GeoDataFrame | None = None,
    metadata: dict[str, Any] | None = None,
) -> MapData:
    """Build a domain MapData aggregate from the current pipeline inputs.

    This keeps the orchestration layer free from direct GIS dependencies while
    allowing the rest of the application to work with domain objects.
    """

    cache_manager = get_cache_manager()
    serializer = PickleSerializer[MapData]()
    cache_inputs = {
        "bounds": None,
        "place": place or "",
        "roads_gdf": fingerprint_geodataframe(roads_gdf) if roads_gdf is not None else None,
        "metadata": metadata or {},
    }
    if bounds is not None:
        cache_inputs["bounds"] = {
            "bounds": [float(v) for v in bounds.total_bounds],
            "crs": str(bounds.crs) if bounds.crs is not None else None,
        }

    cache_key = cache_manager.build_key(
        cache_inputs,
        provider="domain_adapter",
        algorithm_version=_MAPDATA_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="mapdata",
    )
    cached = cache_manager.get(namespace=_MAPDATA_CACHE_NAMESPACE, key=cache_key, serializer=serializer)
    if cached is not None:
        return cached[0]

    if bounds is not None:
        min_x, min_y, max_x, max_y = bounds.total_bounds
        bounding_box = BoundingBox(float(min_x), float(min_y), float(max_x), float(max_y))
    else:
        bounding_box = None

    roads = geodataframe_to_roads(roads_gdf) if roads_gdf is not None else []
    map_data = MapData(
        roads=roads,
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
            format_version="1",
            extra={"road_count": int(len(map_data.roads))},
        ),
    )
    return map_data
