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
from osm2terrn.processing.network.road_network_export import build_roads_from_graph
from osm2terrn.utils.geometry.bounds import compute_world_params, make_square_bounds_centered
from osm2terrn.utils.logger import get_logger, log_info, log_warning
from osm2terrn.processing.terrain.terrn2_entrypoint import export_terrn2_entrypoint
from osm2terrn.domain.adapters.bounds import require_domain_bounding_box, to_domain_bounding_box
from osm2terrn.domain.adapters.osmnx_to_map import build_mapdata_from_pipeline_context
from osm2terrn.domain.adapters.osmnx_to_roads import graph_to_roads_geodataframe
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.data.acquisition import LayerAcquisitionResult
from osm2terrn.data.street_network import StreetNetworkResult

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


def _resolve_square_bounds(bounds: BoundingBox, page_size: Optional[int] = None) -> BoundingBox:
    domain_bounds = require_domain_bounding_box(bounds)

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
    bounds: BoundingBox,
    place: str,
    elevation_data: Optional[dict[str, Any]] = None,
) -> tuple[str, str, dict[str, Any]]:
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
            "elevation_status": "failed",
        }
    return heightmap_path, groundmap_path, elevation_stats


def _export_roads(
    place: str,
    origin_lon: float,
    origin_lat: float,
    min_elevation: float,
    target_bounds: BoundingBox,
    domain_map: Any,
    road_network: StreetNetworkResult | None,
    include_roads: bool,
    output_dir: str | None = None,
) -> Optional[str]:
    if not include_roads:
        domain_map.metadata["road_processing_status"] = "not_started"
        domain_map.metadata["road_export_status"] = "disabled"
        domain_map.metadata["roads_exported"] = False
        return None

    if road_network is None:
        domain_map.metadata["road_processing_status"] = "not_started"
        domain_map.metadata["road_export_status"] = "skipped"
        domain_map.metadata["road_acquisition_status"] = "missing"
        domain_map.metadata["roads_exported"] = False
        log_warning(logger, "Skipping roads export: no street acquisition result was supplied.")
        return None

    try:
        road_network.validate()
    except Exception as exc:
        domain_map.metadata["road_export_status"] = "failed"
        domain_map.metadata["road_processing_status"] = "failed"
        domain_map.metadata["roads_exported"] = False
        log_warning(logger, f"Skipping roads export: invalid street result ({type(exc).__name__}).")
        return None

    domain_map.metadata["road_acquisition_status"] = road_network.status
    if road_network.diagnostic:
        domain_map.metadata["road_acquisition_diagnostic"] = road_network.diagnostic
    if road_network.status != "available":
        domain_map.metadata["road_processing_status"] = "not_started"
        domain_map.metadata["road_export_status"] = "skipped"
        domain_map.metadata["roads_exported"] = False
        if road_network.status in {"failed", "missing"}:
            log_warning(logger, f"Skipping roads export: acquisition status is {road_network.status}.")
        return None

    if domain_map.metadata.get("road_mapdata_status") == "failed":
        domain_map.metadata["road_processing_status"] = "failed"
        domain_map.metadata["road_export_status"] = "failed"
        domain_map.metadata["roads_exported"] = False
        log_warning(logger, "Skipping roads export: street graph to MapData conversion failed.")
        return None

    try:
        filename_prefix = _normalize_place_for_filename(place)
        graph = road_network.graph
        if graph is None:
            raise ValueError("Available street result has no graph")
        roads_tobj_path = build_roads_from_graph(
            graph=graph,
            origin_lon=origin_lon,
            origin_lat=origin_lat,
            place=place,
            tobj_prefix=filename_prefix,
            min_elevation=min_elevation,
            target_bounds=target_bounds,
            output_dir=output_dir or _get_output_dir(),
        )
        domain_map.metadata["road_processing_status"] = "available"
        if roads_tobj_path:
            domain_map.metadata["road_export_status"] = "exported"
        else:
            domain_map.metadata["road_processing_status"] = "empty"
            domain_map.metadata["road_export_status"] = "skipped"
        domain_map.metadata["roads_exported"] = bool(roads_tobj_path)
        log_info(logger, f"Procedural roads exported to: {roads_tobj_path}")
        return roads_tobj_path
    except Exception as exc:
        domain_map.metadata["road_processing_status"] = "failed"
        domain_map.metadata["road_export_status"] = "failed"
        domain_map.metadata["roads_exported"] = False
        log_warning(logger, f"Road processing or export failed ({type(exc).__name__}).")
        return None


def export_terrain_assets(
    place: str,
    bounds: BoundingBox,
    elevation_data: Optional[dict[str, Any]] = None,
    origin_lon: float = 0.0,
    origin_lat: float = 0.0,
    target_bounds: Optional[BoundingBox] = None,
    road_network: StreetNetworkResult | None = None,
    acquisition_results: dict[str, LayerAcquisitionResult] | None = None,
    terrain_world_size: int | None = None,
) -> dict[str, Optional[str]]:
    domain_bounds = require_domain_bounding_box(bounds)
    domain_target_bounds = require_domain_bounding_box(target_bounds) if target_bounds is not None else domain_bounds
    if terrain_world_size is None:
        world_size, _ = compute_world_params(
            domain_bounds,
            page_size=_PROJECT_CONFIG.terrain.page_size,
            snap_to_pow2=True,
        )
    else:
        if terrain_world_size <= 0:
            raise ValueError("Terrain world size must be a positive number of meters")
        world_size = terrain_world_size

    include_roads = bool(_PROJECT_CONFIG.export.include_roads)
    include_buildings = bool(_PROJECT_CONFIG.export.include_buildings)
    roads_gdf = None
    road_mapdata_status = "disabled" if not include_roads else ("missing" if road_network is None else "not_started")
    acquisition_status = "missing"
    mapdata_diagnostic: str | None = None
    if include_roads and road_network is not None:
        try:
            if not isinstance(road_network, StreetNetworkResult):
                raise TypeError("Road bundle entry is not a StreetNetworkResult")
            road_network.validate()
            acquisition_status = road_network.status
        except Exception as exc:
            road_mapdata_status = "failed"
            acquisition_status = "failed"
            mapdata_diagnostic = f"{type(exc).__name__}: invalid street acquisition result"
            log_warning(logger, f"Invalid street acquisition result ({type(exc).__name__}).")
        else:
            if road_network.status == "available":
                # A conversion failure is not an acquisition failure: keep acquisition status intact.
                try:
                    graph = road_network.graph
                    if graph is None:
                        raise ValueError("Available street result has no graph")
                    roads_gdf = graph_to_roads_geodataframe(graph)
                    road_mapdata_status = "available"
                except Exception as exc:
                    road_mapdata_status = "failed"
                    mapdata_diagnostic = f"{type(exc).__name__}: street graph to MapData conversion failed"
                    log_warning(logger, f"Could not adapt street graph to MapData ({type(exc).__name__}).")
            else:
                road_mapdata_status = road_network.status

    domain_map = build_mapdata_from_pipeline_context(
        bounds=domain_bounds,
        place=place,
        roads_gdf=roads_gdf,
        metadata={
            "origin_lon": origin_lon,
            "origin_lat": origin_lat,
            "road_acquisition_status": acquisition_status,
            "road_mapdata_status": road_mapdata_status,
            "road_processing_status": "not_started",
            "road_export_status": "disabled" if not include_roads else "not_started",
        },
    )
    serialized_acquisition_results: dict[str, dict[str, str | None]] = {}
    acquisition_warnings: list[str] = []
    for layer_name, result in (acquisition_results or {}).items():
        if not isinstance(result, LayerAcquisitionResult):
            raise TypeError(f"Acquisition result for {layer_name!r} has an invalid type")
        serialized_acquisition_results[layer_name] = {
            "status": result.status,
            "source": result.source,
            "failure_category": result.failure_category,
            "failure_stage": result.failure_stage,
            "diagnostic": result.diagnostic,
        }
        if result.status == "failed":
            detail = result.diagnostic or "unknown acquisition failure"
            acquisition_warnings.append(f"{layer_name}: {detail}")
    domain_map.metadata["layer_acquisition_results"] = serialized_acquisition_results
    domain_map.metadata["building_export_status"] = (
        "not_implemented" if include_buildings else "disabled"
    )
    domain_map.metadata["elevation_status"] = "not_started"
    if mapdata_diagnostic:
        domain_map.metadata["road_mapdata_diagnostic"] = mapdata_diagnostic
    domain_map.metadata.setdefault("pipeline_mode", "roads_and_buildings")
    domain_map.metadata["building_count"] = len(domain_map.buildings)
    domain_map.metadata["road_count"] = len(domain_map.roads)

    output_dir = _get_output_dir()
    heightmap_path, groundmap_path, elevation_stats = _export_heightmap_textures(
        bounds=domain_bounds,
        place=place,
        elevation_data=elevation_data,
    )
    elevation_status = str(elevation_stats.get("elevation_status", "available"))
    domain_map.metadata["elevation_status"] = elevation_status

    roads_tobj_path = _export_roads(
        place=place,
        origin_lon=origin_lon,
        origin_lat=origin_lat,
        min_elevation=float(elevation_stats.get("min_elevation", 0.0)),
        target_bounds=domain_target_bounds,
        domain_map=domain_map,
        road_network=road_network,
        include_roads=include_roads,
        output_dir=output_dir,
    )

    filename_prefix = _normalize_place_for_filename(place)
    world_size_y = calculate_world_size_y(
        min_elevation=float(elevation_stats.get("min_elevation", 0.0)),
        max_elevation=float(elevation_stats.get("max_elevation", 0.0)),
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

    roads_outcome = _roads_outcome(domain_map.metadata)
    partial_reasons: list[str] = []
    if include_roads and roads_outcome == "not_requested":
        partial_reasons.append(
            "roads were NOT exported because the OSM network configuration marked them not requested"
        )
    elif include_roads and roads_outcome == "failed":
        partial_reasons.append("roads were NOT exported")
    if include_buildings:
        partial_reasons.append("building export is not implemented")
    if elevation_status == "failed":
        partial_reasons.append("elevation acquisition failed; a flat fallback heightmap was used")
    export_outcome = "partial" if partial_reasons else "complete"

    return {
        "terrn2": terrn2,
        "global_otc": global_otc,
        "page_otc": page_otc,
        "heightmap": heightmap_path,
        "groundmap": groundmap_path,
        "tobj": tobj_path,
        "roads_tobj": roads_tobj_path,
        "roads_outcome": roads_outcome,
        "buildings_outcome": domain_map.metadata["building_export_status"],
        "elevation_outcome": elevation_status,
        "export_outcome": export_outcome,
        "partial_reasons": "; ".join(partial_reasons) or None,
        "acquisition_warnings": "; ".join(acquisition_warnings) or None,
    }


def _roads_outcome(metadata: dict[str, Any]) -> str:
    """Summarize the road stage for callers.

    Acquisition, MapData conversion and export statuses stay separate in
    metadata. With roads enabled, ``failed`` means requested roads were lost to a
    failure or a missing acquisition result (``road_network is None`` is never a
    valid acquisition outcome), and ``not_requested`` means the configured OSM
    networks omit roads although export was enabled. ``empty`` stays a success.
    """
    export_status = str(metadata.get("road_export_status", "not_started"))
    if export_status == "disabled":
        return "disabled"
    acquisition_status = metadata.get("road_acquisition_status")
    if export_status == "failed" or acquisition_status in {"failed", "missing"}:
        return "failed"
    if acquisition_status == "not_requested":
        return "not_requested"
    return export_status
