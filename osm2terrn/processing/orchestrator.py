from __future__ import annotations

import os
import re
from typing import Any, Optional

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.config.settings import get_program_config, get_project_config
from osm2terrn.processing.terrain.heightmap_handler import generate_heightmap_n_texture
from osm2terrn.processing.otc.otc_global import export_global_otc
from osm2terrn.processing.otc.otc_paged import export_paged_otc
from osm2terrn.processing.terrain.elevation_scaling import calculate_world_size_y
from osm2terrn.processing.network.road_network_export import build_roads_from_place
from osm2terrn.utils.geometry.bounds import compute_world_params, make_square_bounds_centered
from osm2terrn.utils.logger import get_logger, log_info, log_warning
from osm2terrn.processing.terrain.terrn2_entrypoint import export_terrn2_entrypoint
from osm2terrn.domain.adapters.bounds import to_domain_bounding_box
from osm2terrn.domain.adapters.osmnx_to_map import build_mapdata_from_pipeline_context

logger = get_logger("export_orchestrator")
_PROGRAM_CONFIG = get_program_config()
_PROJECT_CONFIG = get_project_config()
_DOMAIN_MANIFEST_NAMESPACE = "exports/tobj/domain-manifest"
_DOMAIN_MANIFEST_ALGORITHM_VERSION = "1"


def _normalize_place_for_filename(place: str) -> str:
    """Return a safe filename prefix using only the city name from a full place string."""
    if not place:
        return _PROGRAM_CONFIG.terrain_runtime.default_place_name

    city_name = place.split(",")[0].strip()
    if not city_name:
        return _PROGRAM_CONFIG.terrain_runtime.default_place_name

    safe_name = re.sub(r'[<>:"/\\|?*]', "", city_name)
    return safe_name or _PROGRAM_CONFIG.terrain_runtime.default_place_name


def _get_output_dir() -> str:
    output_dir = str(_PROGRAM_CONFIG.paths.output_dir.resolve())
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _resolve_square_bounds(bounds_gdf: Any, page_size: Optional[int] = None) -> Any:
    if bounds_gdf is None:
        raise ValueError("Bounds are required for export.")

    domain_bounds = to_domain_bounding_box(bounds_gdf)
    if domain_bounds is None:
        raise ValueError("Bounds are required for export.")

    resolved_page_size = page_size or _PROJECT_CONFIG.terrain.page_size
    world_size, _ = compute_world_params(domain_bounds, page_size=resolved_page_size, snap_to_pow2=True)
    return make_square_bounds_centered(domain_bounds, world_size)


def _write_domain_objects_manifest(domain_map: Any, output_path: str) -> str:
    """Persist a lightweight .tobj manifest derived from the domain aggregate."""
    roads = getattr(domain_map, "roads", None) or []
    buildings = getattr(domain_map, "buildings", None) or []
    cache_manager = get_cache_manager()
    serializer = PickleSerializer[str]()
    cache_key = cache_manager.build_key(
        {
            "roads": [
                {
                    "id": str(getattr(road, "id", "unknown")),
                    "width": getattr(road, "width", None),
                    "surface": getattr(road, "surface", None),
                }
                for road in roads
            ],
            "buildings": [
                {
                    "id": str(getattr(building, "id", "unknown")),
                    "height": getattr(building, "height", None),
                }
                for building in buildings
            ],
        },
        provider="export",
        algorithm_version=_DOMAIN_MANIFEST_ALGORITHM_VERSION,
        format_version="1",
        artifact_type="domain_manifest_payload",
    )
    cached = cache_manager.get(namespace=_DOMAIN_MANIFEST_NAMESPACE, key=cache_key, serializer=serializer)
    if cached is not None:
        content = cached[0]
    else:
        lines = [
            "// Domain-derived object manifest",
            f"// roads={len(roads)}",
            f"// buildings={len(buildings)}",
        ]

        for road in roads:
            lines.append(
                f"// road:{getattr(road, 'id', 'unknown')} width={getattr(road, 'width', None)} surface={getattr(road, 'surface', None)}"
            )

        for building in buildings:
            lines.append(
                f"// building:{getattr(building, 'id', 'unknown')} height={getattr(building, 'height', None)}"
            )
        content = "\n".join(lines) + "\n"
        cache_manager.put(
            namespace=_DOMAIN_MANIFEST_NAMESPACE,
            key=cache_key,
            value=content,
            serializer=serializer,
            metadata=CacheMetadata(
                artifact_type="domain_manifest_payload",
                provider="export",
                algorithm_version=_DOMAIN_MANIFEST_ALGORITHM_VERSION,
                format_version="1",
                extra={"roads": int(len(roads)), "buildings": int(len(buildings))},
            ),
        )

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(content)

    return output_path


def _export_heightmap_textures(
    bounds: Any,
    place: str,
    elevation_data: Optional[dict[str, Any]] = None,
) -> tuple[str, str, dict[str, float]]:
    output_dir = _get_output_dir()
    filename_prefix = _normalize_place_for_filename(place)
    heightmap_path = os.path.join(output_dir, f"{filename_prefix}_heightmap.png")
    groundmap_path = os.path.join(output_dir, f"{filename_prefix}_groundmap.png")

    elevation_stats = generate_heightmap_n_texture(
        bounds,
        heightmap_path=heightmap_path,
        groundmap_path=groundmap_path,
        elevation_data=elevation_data,
    )
    if elevation_stats is None:
        elevation_stats = {
            "min_elevation": 0.0,
            "max_elevation": 0.0,
            "elevation_range": 0.0,
        }
    return heightmap_path, groundmap_path, elevation_stats


def _export_roads(
    place: str,
    origin_lon: float,
    origin_lat: float,
    min_elevation: float,
    target_bounds: Any,
    domain_map: Any,
) -> Optional[str]:
    road_entities = getattr(domain_map, "roads", None) or []
    if not road_entities:
        domain_map.metadata["roads_exported"] = False
        log_info(logger, "Skipping roads export: MapData contains no road entities.")
        return None

    if not place or (origin_lon == 0.0 and origin_lat == 0.0):
        log_warning(logger, "Skipping roads export: missing origin coordinates.")
        return None

    try:
        filename_prefix = _normalize_place_for_filename(place)
        roads_tobj_path = build_roads_from_place(
            place,
            origin_lon,
            origin_lat,
            tobj_prefix=filename_prefix,
            min_elevation=min_elevation,
            target_bounds=target_bounds,
        )
        domain_map.metadata["roads_exported"] = bool(roads_tobj_path)
        log_info(logger, f"Procedural roads exported to: {roads_tobj_path}")
        return roads_tobj_path
    except Exception as exc:
        log_warning(logger, f"Skipping roads export due to error: {exc}")
        return None


def export_terrain_assets(
    place: str,
    bounds: Any,
    elevation_data: Optional[dict[str, Any]] = None,
    origin_lon: float = 0.0,
    origin_lat: float = 0.0,
    target_bounds: Any = None,
) -> dict[str, Optional[str]]:
    domain_map = build_mapdata_from_pipeline_context(
        bounds=bounds if not isinstance(bounds, (str, tuple, list)) else None,
        place=place,
        metadata={"origin_lon": origin_lon, "origin_lat": origin_lat},
    )
    if hasattr(bounds, "_buildings_gdf"):
        try:
            buildings_gdf = getattr(bounds, "_buildings_gdf", None)
            if buildings_gdf is not None:
                from osm2terrn.domain.adapters.osmnx_to_buildings import geodataframe_to_buildings

                domain_map.buildings = geodataframe_to_buildings(buildings_gdf)
        except Exception:
            pass
    domain_map.metadata.setdefault("pipeline_mode", "roads_and_buildings")
    domain_map.metadata["building_count"] = len(domain_map.buildings)
    domain_map.metadata["road_count"] = len(domain_map.roads)

    output_dir = _get_output_dir()
    heightmap_path, groundmap_path, elevation_stats = _export_heightmap_textures(
        bounds=bounds,
        place=place,
        elevation_data=elevation_data,
    )

    roads_tobj_path = _export_roads(
        place=place,
        origin_lon=origin_lon,
        origin_lat=origin_lat,
        min_elevation=elevation_stats.get("min_elevation", 0.0),
        target_bounds=target_bounds,
        domain_map=domain_map,
    )

    filename_prefix = _normalize_place_for_filename(place)
    domain_bounds = to_domain_bounding_box(bounds)
    if domain_bounds is None:
        initial_bounds = None
        world_size = _PROJECT_CONFIG.terrain.page_size
    else:
        initial_bounds = domain_bounds
        world_size, _ = compute_world_params(
            initial_bounds,
            page_size=_PROJECT_CONFIG.terrain.page_size,
            snap_to_pow2=True,
        )
    world_size_y = calculate_world_size_y(
        min_elevation=elevation_stats.get("min_elevation"),
        max_elevation=elevation_stats.get("max_elevation"),
    )

    page_otc = os.path.join(output_dir, f"{filename_prefix}-page-0-0.otc")
    export_paged_otc(
        str(page_otc),
        heightmap_png=os.path.basename(heightmap_path),
        groundmap_file=os.path.basename(groundmap_path),
    )

    global_otc = os.path.join(output_dir, f"{filename_prefix}.otc")
    export_global_otc(
        filepath=str(global_otc),
        page_file_format=f"{filename_prefix}-page-0-0.otc",
        world_size_x=float(world_size),
        world_size_z=float(world_size),
        world_size_y=world_size_y,
        pages_x=0,
        pages_z=0,
    )

    terrn2 = os.path.join(output_dir, f"{filename_prefix}.terrn2")
    tobj_path = os.path.join(output_dir, f"{filename_prefix}.tobj")
    _write_domain_objects_manifest(domain_map, tobj_path)

    objects_files = [os.path.basename(tobj_path)]
    if roads_tobj_path and os.path.exists(roads_tobj_path):
        objects_files.append(os.path.basename(roads_tobj_path))

    export_terrn2_entrypoint(
        filepath=str(terrn2),
        terrain_name=place,
        geometry_config=os.path.basename(global_otc),
        objects_files=objects_files,
        elevation_stats=elevation_stats,
        authors=[
            "osm2terrn",
            "OpenStreetMap Contributors",
            "YourNickHere",
        ],
    )

    return {
        "terrn2": terrn2,
        "global_otc": global_otc,
        "page_otc": page_otc,
        "heightmap": heightmap_path,
        "groundmap": groundmap_path,
        "tobj": tobj_path,
        "roads_tobj": roads_tobj_path,
    }
