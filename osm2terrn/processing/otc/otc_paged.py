import os
from typing import Dict, List, Optional
from osm2terrn.cache.metadata import CacheMetadata
from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.config.cache import get_cache_manager
from osm2terrn.config.settings import get_program_config
from osm2terrn.utils.logger import get_logger, log_info, log_error

logger = get_logger("otc_paged")
_PROGRAM_CONFIG = get_program_config()
_OTC_PAGED_PAYLOAD_NAMESPACE = "exports/otc/paged-payload"
_OTC_PAGED_ALGORITHM_VERSION = "1"


def _render_paged_otc_content(
    heightmap_png: str,
    base_layer: dict[str, object],
    layers: list[dict[str, object]],
) -> str:
    lines: list[str] = []
    total_layers = 1 + (len(layers) if layers else 0)
    lines.append(f"{os.path.basename(heightmap_png)}")
    lines.append(f"{total_layers}")
    lines.append("; worldSize, diffusespecular, normalheight, blendmap, blendmapmode, alpha")
    lines.append(f"{int(base_layer['worldSize'])}, {base_layer['diffuse']}, {base_layer['normal']}")
    for layer in (layers or []):
        world_size = int(str(layer.get("worldSize", _PROGRAM_CONFIG.otc_runtime.default_base_layer_world_size)))
        diffuse = str(layer.get("diffuse", _PROGRAM_CONFIG.otc_runtime.default_detail_diffuse_texture))
        normal = str(layer.get("normal", _PROGRAM_CONFIG.otc_runtime.default_normal_texture))
        blend = layer.get("blend")
        blendmode = str(layer.get("blendmode", "R"))
        alpha = float(str(layer.get("alpha", _PROGRAM_CONFIG.otc_runtime.default_layer_alpha)))
        if blend is None:
            lines.append(f"{world_size}, {diffuse}, {normal}")
        else:
            lines.append(f"{world_size}, {diffuse}, {normal}, {os.path.basename(str(blend))}, {blendmode}, {alpha}")
    lines.append("")
    return "\n".join(lines) + "\n"


def export_paged_otc(
    filepath: str,
    heightmap_png: str,
    groundmap_file: Optional[str] = None,
    layers: Optional[List[Dict[str, object]]] = None,
) -> None:
    try:
        if groundmap_file:
            base_layer = {
                "worldSize": _PROGRAM_CONFIG.otc_runtime.default_groundmap_base_layer_world_size,
                "diffuse": os.path.basename(groundmap_file),
                "normal": _PROGRAM_CONFIG.otc_runtime.default_normal_texture,
            }
        else:
            base_layer = {
                "worldSize": _PROGRAM_CONFIG.otc_runtime.default_base_layer_world_size,
                "diffuse": _PROGRAM_CONFIG.otc_runtime.default_detail_diffuse_texture,
                "normal": _PROGRAM_CONFIG.otc_runtime.default_normal_texture,
            }

        if layers is None:
            layers = []
            if groundmap_file:
                gm = os.path.basename(groundmap_file)
                layers = [
                    {
                        "worldSize": _PROGRAM_CONFIG.otc_runtime.default_base_layer_world_size,
                        "diffuse": _PROGRAM_CONFIG.otc_runtime.default_detail_diffuse_texture,
                        "normal": _PROGRAM_CONFIG.otc_runtime.default_normal_texture,
                        "blend": gm,
                        "blendmode": "G",
                        "alpha": _PROGRAM_CONFIG.otc_runtime.default_layer_alpha,
                    },
                ]

        total_layers = 1 + (len(layers) if layers else 0)
        if total_layers < 1 or total_layers > 6:
            log_error(logger, f"Paged .otc layers must be in range 1-6; got {total_layers}.")
            total_layers = max(1, min(total_layers, 6))
            if layers and (1 + len(layers)) > 6:
                layers = layers[:5]

        cache_manager = get_cache_manager()
        serializer = PickleSerializer[str]()
        cache_key = cache_manager.build_key(
            {
                "heightmap_png": os.path.basename(heightmap_png),
                "base_layer": base_layer,
                "layers": layers or [],
            },
            provider="export",
            algorithm_version=_OTC_PAGED_ALGORITHM_VERSION,
            format_version="1",
            artifact_type="otc_paged_payload",
        )
        cached = cache_manager.get(
            namespace=_OTC_PAGED_PAYLOAD_NAMESPACE,
            key=cache_key,
            serializer=serializer,
        )
        if cached is not None:
            content = cached[0]
        else:
            content = _render_paged_otc_content(
                heightmap_png=heightmap_png,
                base_layer=base_layer,
                layers=layers or [],
            )
            cache_manager.put(
                namespace=_OTC_PAGED_PAYLOAD_NAMESPACE,
                key=cache_key,
                value=content,
                serializer=serializer,
                metadata=CacheMetadata(
                    artifact_type="otc_paged_payload",
                    provider="export",
                    algorithm_version=_OTC_PAGED_ALGORITHM_VERSION,
                    format_version="1",
                ),
            )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        log_info(logger, f"Exported paged .otc to {filepath}")
    except Exception as e:
        log_error(logger, f"Failed to export paged .otc: {e}")
