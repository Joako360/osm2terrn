from typing import Any, Dict, List, Optional

from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_info, log_error
from osm2terrn.processing.terrain.terrn2_water import prepare_water_config, _generate_guid

logger = get_logger("terrn2_entrypoint")
_PROGRAM_CONFIG = get_program_config()
_TERRN2_PAYLOAD_NAMESPACE = "exports/terrn2/payload"
_TERRN2_ALGORITHM_VERSION = "1"


def _render_terrn2_content(
    terrain_name: str,
    geometry_config: str,
    objects_files: List[str],
    authors: Optional[Any],
    water_enabled: int,
    water_line: float,
    water_bottom_line: float,
    ambient_color: str,
    start_position: str,
    start_rotation: float,
    gravity: float,
    category_id: int,
    guid: str,
    sandstorm_cubemap: str,
    caelum_config: Optional[str],
    traction_map: Optional[str],
    scripts: Optional[List[str]],
    asset_packs: Optional[List[str]],
    ai_presets: Optional[List[str]],
    extra_sections: Optional[Dict[str, Dict[str, str]]],
) -> str:
    lines: list[str] = []
    lines.append("[General]")
    lines.append(f"Name = {terrain_name}")
    lines.append(f"GeometryConfig = {geometry_config}")
    lines.append(f"Water = {water_enabled}")
    lines.append(f"WaterLine = {water_line:.6f}")
    lines.append(f"WaterBottomLine = {water_bottom_line:.6f}")
    lines.append(f"AmbientColor = {ambient_color}")
    lines.append(f"StartPosition = {start_position}")
    lines.append(f"StartRotation = {start_rotation:.6f}")
    lines.append(f"Gravity = {gravity:.6f}")
    lines.append(f"CategoryID = {category_id}")
    lines.append(f"Version = {_PROGRAM_CONFIG.terrn2_runtime.default_version}")
    lines.append(f"GUID = {guid}")
    lines.append(f"SandStormCubeMap = {sandstorm_cubemap}")
    if caelum_config:
        lines.append(f"CaelumConfigFile = {caelum_config}")
    if traction_map:
        lines.append(f"TractionMap = {traction_map}")
    lines.append("")

    if authors:
        lines.append("[Authors]")
        if isinstance(authors, list):
            for author in authors:
                lines.append(str(author))
        elif isinstance(authors, dict):
            for role, name in authors.items():
                lines.append(f"{role} = {name}")
        lines.append("")

    if asset_packs:
        lines.append("[AssetPacks]")
        for asset_pack in asset_packs:
            lines.append(f"{asset_pack}=")
        lines.append("")

    lines.append("[Objects]")
    for obj_file in objects_files:
        lines.append(f"{obj_file}=")
    lines.append("")

    if scripts:
        lines.append("[Scripts]")
        for script in scripts:
            lines.append(f"{script}=")
        lines.append("")

    if ai_presets:
        lines.append("[AI Presets]")
        for preset in ai_presets:
            lines.append(f"{preset}=")
        lines.append("")

    if extra_sections:
        for section, values in extra_sections.items():
            lines.append(f"[{section}]")
            for key, value in values.items():
                lines.append(f"{key} = {value}")
            lines.append("")

    return "\n".join(lines) + "\n"


def export_terrn2_entrypoint(
    filepath: str,
    terrain_name: str,
    geometry_config: str,
    objects_files: List[str],
    authors: Optional[Any] = None,
    water_config: Optional[Dict[str, float]] = None,
    elevation_stats: Optional[Dict[str, float]] = None,
    ambient_color: Optional[str] = None,
    start_position: Optional[str] = None,
    start_rotation: Optional[float] = None,
    sandstorm_cubemap: Optional[str] = None,
    gravity: Optional[float] = None,
    category_id: Optional[int] = None,
    guid: Optional[str] = None,
    caelum_config: Optional[str] = None,
    traction_map: Optional[str] = None,
    scripts: Optional[List[str]] = None,
    asset_packs: Optional[List[str]] = None,
    ai_presets: Optional[List[str]] = None,
    extra_sections: Optional[Dict[str, Dict[str, str]]] = None,
) -> None:
    try:
        processed_water_config = prepare_water_config(elevation_stats, water_config)
        water_enabled = 1 if processed_water_config.get("enabled", True) else 0
        water_line = processed_water_config.get(
            "water_line",
            _PROGRAM_CONFIG.water_runtime.default_water_line,
        )
        water_bottom_line = processed_water_config.get(
            "water_bottom_line",
            _PROGRAM_CONFIG.water_runtime.default_water_bottom_line,
        )

        ambient_color = ambient_color or _PROGRAM_CONFIG.terrn2_runtime.default_ambient_color
        start_position = start_position or _PROGRAM_CONFIG.terrn2_runtime.default_start_position
        start_rotation = (
            start_rotation
            if start_rotation is not None
            else _PROGRAM_CONFIG.terrn2_runtime.default_start_rotation
        )
        sandstorm_cubemap = (
            sandstorm_cubemap or _PROGRAM_CONFIG.terrn2_runtime.default_sandstorm_cubemap
        )
        gravity = gravity if gravity is not None else _PROGRAM_CONFIG.terrn2_runtime.default_gravity
        category_id = (
            category_id
            if category_id is not None
            else _PROGRAM_CONFIG.terrn2_runtime.default_category_id
        )

        if not guid:
            guid = _generate_guid()
            log_info(logger, f"🔑 Generated GUID: {guid}")

        cache_manager = get_cache_manager()
        serializer = PickleSerializer[str]()
        cache_key = cache_manager.build_key(
            {
                "terrain_name": terrain_name,
                "geometry_config": geometry_config,
                "objects_files": objects_files,
                "authors": authors,
                "water_enabled": water_enabled,
                "water_line": float(water_line),
                "water_bottom_line": float(water_bottom_line),
                "ambient_color": ambient_color,
                "start_position": start_position,
                "start_rotation": float(start_rotation),
                "sandstorm_cubemap": sandstorm_cubemap,
                "gravity": float(gravity),
                "category_id": int(category_id),
                "guid": guid,
                "caelum_config": caelum_config,
                "traction_map": traction_map,
                "scripts": scripts or [],
                "asset_packs": asset_packs or [],
                "ai_presets": ai_presets or [],
                "extra_sections": extra_sections or {},
            },
            provider="export",
            algorithm_version=_TERRN2_ALGORITHM_VERSION,
            format_version="1",
            artifact_type="terrn2_payload",
        )
        cached = cache_manager.get(
            namespace=_TERRN2_PAYLOAD_NAMESPACE,
            key=cache_key,
            serializer=serializer,
        )
        if cached is not None:
            content = cached[0]
        else:
            content = _render_terrn2_content(
                terrain_name=terrain_name,
                geometry_config=geometry_config,
                objects_files=objects_files,
                authors=authors,
                water_enabled=water_enabled,
                water_line=float(water_line),
                water_bottom_line=float(water_bottom_line),
                ambient_color=ambient_color,
                start_position=start_position,
                start_rotation=float(start_rotation),
                gravity=float(gravity),
                category_id=int(category_id),
                guid=guid,
                sandstorm_cubemap=sandstorm_cubemap,
                caelum_config=caelum_config,
                traction_map=traction_map,
                scripts=scripts,
                asset_packs=asset_packs,
                ai_presets=ai_presets,
                extra_sections=extra_sections,
            )
            cache_manager.put(
                namespace=_TERRN2_PAYLOAD_NAMESPACE,
                key=cache_key,
                value=content,
                serializer=serializer,
                metadata=CacheMetadata(
                    artifact_type="terrn2_payload",
                    provider="export",
                    algorithm_version=_TERRN2_ALGORITHM_VERSION,
                    format_version="1",
                ),
            )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        log_info(logger, f"✅ Successfully exported terrn2 entry point to {filepath}")
    except IOError as e:
        log_error(logger, f"❌ I/O error while exporting terrn2: {e}")
        raise
    except Exception as e:
        log_error(logger, f"Unexpected error while exporting terrn2: {e}")
        raise
