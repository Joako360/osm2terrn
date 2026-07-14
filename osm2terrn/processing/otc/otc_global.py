from typing import Any, Dict, List, Optional
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_info, log_error

logger = get_logger("otc_global")
_PROGRAM_CONFIG = get_program_config()
_OTC_GLOBAL_PAYLOAD_NAMESPACE = "exports/otc/global-payload"
_OTC_GLOBAL_ALGORITHM_VERSION = "1"


def _render_global_otc_content(
    page_file_format: str,
    world_size_x: float,
    world_size_z: float,
    world_size_y: float,
    page_size: int,
    heightmap: Optional[Dict[str, Any]],
    disable_caching: bool,
    extra_settings: Optional[Dict[str, str]],
) -> str:
    lines: list[str] = []
    if heightmap:
        fmt = str(heightmap.get("format", "raw")).lower()
        if fmt == "raw":
            size = int(heightmap.get("size", page_size))
            bpp = int(heightmap.get("bpp", 2))
            flip_x = 1 if bool(heightmap.get("flip_x", False)) else 0
            lines.append(f"Heightmap.0.0.raw.size={size}")
            lines.append(f"Heightmap.0.0.raw.bpp={bpp}")
            lines.append(f"Heightmap.0.0.flipX={flip_x}")
            lines.append("")

    lines.append(f"WorldSizeX={int(world_size_x)}")
    lines.append(f"WorldSizeZ={int(world_size_z)}")
    lines.append(f"WorldSizeY={int(world_size_y)}")
    lines.append(f"PageSize={int(page_size)}")
    lines.append(" ")
    lines.append("disableCaching=1" if disable_caching else "disableCaching=0")
    lines.append(" ")
    lines.append(f"PageFileFormat={page_file_format}")
    lines.append("")
    lines.append("MaxPixelError=1")
    lines.append("LightmapEnabled=0")
    lines.append("SpecularMappingEnabled=1")
    lines.append("NormalMappingEnabled=1")
    if extra_settings:
        for key, value in extra_settings.items():
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def export_global_otc(
    filepath: str,
    page_file_format: str,
    world_size_x: float,
    world_size_z: float,
    world_size_y: float = _PROGRAM_CONFIG.otc_runtime.default_world_size_y,
    page_size: int = _PROGRAM_CONFIG.otc_runtime.default_page_size,
    pages_x: int = 0,
    pages_z: int = 0,
    heightmap: Optional[Dict[str, Any]] = None,
    layer_blend_map_size: int = _PROGRAM_CONFIG.otc_runtime.layer_blend_map_size,
    min_batch_size: int = _PROGRAM_CONFIG.otc_runtime.min_batch_size,
    max_batch_size: int = _PROGRAM_CONFIG.otc_runtime.max_batch_size,
    disable_caching: bool = _PROGRAM_CONFIG.otc_runtime.disable_caching,
    extra_settings: Optional[Dict[str, str]] = None,
) -> None:
    try:
        cache_manager = get_cache_manager()
        serializer = PickleSerializer[str]()
        cache_key = cache_manager.build_key(
            {
                "page_file_format": page_file_format,
                "world_size_x": float(world_size_x),
                "world_size_z": float(world_size_z),
                "world_size_y": float(world_size_y),
                "page_size": int(page_size),
                "heightmap": heightmap,
                "disable_caching": bool(disable_caching),
                "extra_settings": extra_settings or {},
            },
            provider="export",
            algorithm_version=_OTC_GLOBAL_ALGORITHM_VERSION,
            format_version="1",
            artifact_type="otc_global_payload",
        )
        cached = cache_manager.get(
            namespace=_OTC_GLOBAL_PAYLOAD_NAMESPACE,
            key=cache_key,
            serializer=serializer,
        )
        if cached is not None:
            content = cached[0]
        else:
            content = _render_global_otc_content(
                page_file_format=page_file_format,
                world_size_x=world_size_x,
                world_size_z=world_size_z,
                world_size_y=world_size_y,
                page_size=page_size,
                heightmap=heightmap,
                disable_caching=disable_caching,
                extra_settings=extra_settings,
            )
            cache_manager.put(
                namespace=_OTC_GLOBAL_PAYLOAD_NAMESPACE,
                key=cache_key,
                value=content,
                serializer=serializer,
                metadata=CacheMetadata(
                    artifact_type="otc_global_payload",
                    provider="export",
                    algorithm_version=_OTC_GLOBAL_ALGORITHM_VERSION,
                    format_version="1",
                ),
            )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        log_info(logger, f"Exported global .otc to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export global .otc: {e}")
