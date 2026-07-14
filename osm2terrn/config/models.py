"""Typed configuration models for osm2terrn."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(slots=True)
class PathConfig:
    """Internal filesystem paths used by the program runtime."""

    workspace_root: Path
    output_dir: Path
    logs_dir: Path
    cache_dir: Path
    projects_dir: Path


@dataclass(slots=True)
class LoggingConfig:
    """Program logging defaults."""

    level: int
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    fmt: str = "[%(asctime)s] %(levelname)s - %(name)s: %(message)s"
    enable_console: bool = True
    enable_file: bool = False
    default_log_file: Path | None = None


@dataclass(slots=True)
class CacheConfig:
    """Internal cache settings."""

    enabled: bool = True
    max_size_mb: int = 512


@dataclass(slots=True)
class ProviderConfig:
    """External provider defaults and integration knobs."""

    opentopo_api_key_env_var: str = "OPENTOPO_ELEVATION_API_KEY"
    overpass_max_query_area_size_env_var: str = "OVERPASS_MAX_QUERY_AREA_SIZE"
    overpass_requests_timeout_env_var: str = "OVERPASS_REQUESTS_TIMEOUT"
    overpass_rate_limit_env_var: str = "OVERPASS_RATE_LIMIT"
    elevation_url_template: str = "https://api.opentopodata.org/v1/test-dataset?locations={locations}"


@dataclass(slots=True)
class OsmConfig:
    """OSM extraction and OSMnx behavior settings."""

    custom_tags: tuple[str, ...]
    map_geometries: dict[str, dict[str, Any]]
    networks: dict[str, str | None]
    max_query_area_size: int = 2_500_000_000
    requests_timeout: int = 1000
    overpass_rate_limit: bool = True
    osmnx_log_console: bool = True
    osmnx_log_file: bool = True
    osmnx_log_level: int = 40


@dataclass(slots=True)
class TerrainRuntimeConfig:
    """Runtime defaults tied to terrain processing internals."""

    output_size: tuple[int, int] = (1025, 1025)
    page_size: int = 1025
    default_colormap: str = "gist_earth"
    default_place_name: str = "terrain"
    default_tobj_prefix: str = "terrain"
    smoothing_sigma: float = 1.0
    default_output_subdir: str = "output"


@dataclass(slots=True)
class WaterRuntimeConfig:
    """Runtime defaults for water and elevation realism."""

    sea_level: float = 0.0
    min_terrain_height_above_water: float = 10.0
    water_elevation_percentile: int = 5
    default_water_depth: float = 150.0
    enable_realistic_water: bool = True
    default_water_enabled: int = 1
    default_water_line: float = 0.0
    default_water_bottom_line: float = -150.0


@dataclass(slots=True)
class ElevationRuntimeConfig:
    """Runtime defaults for elevation scaling and normalization."""

    enable_realistic_elevation: bool = True
    default_world_size_y: float = 300.0
    min_world_size_y: float = 50.0
    max_world_size_y: float = 10000.0
    normalization_tolerance: float = 0.1


@dataclass(slots=True)
class Terrn2RuntimeConfig:
    """Runtime defaults for terrn2 metadata and atmosphere."""

    default_ambient_color: str = "1.0, 1.0, 1.0"
    default_sandstorm_cubemap: str = "tracks/skyboxcol"
    default_start_position: str = "0.0, 0.0, 0.0"
    default_start_rotation: float = 0.0
    default_gravity: float = -9.81
    default_category_id: int = 129
    default_version: int = 2


@dataclass(slots=True)
class OtcRuntimeConfig:
    """Runtime defaults for OTC exporters."""

    default_world_size_y: float = 300.0
    default_page_size: int = 1025
    layer_blend_map_size: int = 1024
    min_batch_size: int = 33
    max_batch_size: int = 65
    disable_caching: bool = True
    default_base_layer_world_size: int = 6
    default_groundmap_base_layer_world_size: int = 8192
    default_layer_alpha: float = 0.5
    default_detail_diffuse_texture: str = "terrain_detail.dds"
    default_normal_texture: str = "blank_NRM.dds"
    legacy_cell_size: float = 2.0
    legacy_texture_repeat: float = 1.0


@dataclass(slots=True)
class ProgramConfig:
    """Configuration internal to osm2terrn itself."""

    paths: PathConfig
    logging: LoggingConfig
    cache: CacheConfig
    providers: ProviderConfig
    osm: OsmConfig
    terrain_runtime: TerrainRuntimeConfig
    water_runtime: WaterRuntimeConfig
    elevation_runtime: ElevationRuntimeConfig
    terrn2_runtime: Terrn2RuntimeConfig
    otc_runtime: OtcRuntimeConfig


@dataclass(slots=True)
class TerrainProjectConfig:
    """Project-specific terrain generation configuration."""

    page_size: int = 1025
    output_size: tuple[int, int] = (1025, 1025)
    colormap: str = "gist_earth"
    smoothing_sigma: float = 1.0


@dataclass(slots=True)
class RoadsProjectConfig:
    """Project-specific roads configuration."""

    network_type: str = "drive"
    simplify: bool = True
    default_width: float = 7.0
    default_border_width: float = 0.0
    default_border_height: float = 0.0


@dataclass(slots=True)
class BuildingsProjectConfig:
    """Project-specific buildings configuration placeholder."""

    enabled: bool = True


@dataclass(slots=True)
class MaterialsProjectConfig:
    """Project-specific materials configuration placeholder."""

    default_ground_texture: str = "terrain_detail.dds"


@dataclass(slots=True)
class ExportProjectConfig:
    """Project-specific export configuration."""

    output_name: str = "terrain"
    include_roads: bool = True
    include_buildings: bool = True


@dataclass(slots=True)
class PipelineProjectConfig:
    """Project-specific pipeline configuration."""

    preload_elevation: bool = True


@dataclass(slots=True)
class ProjectConfig:
    """Configuration describing how to build a concrete terrain project."""

    terrain: TerrainProjectConfig = field(default_factory=TerrainProjectConfig)
    roads: RoadsProjectConfig = field(default_factory=RoadsProjectConfig)
    buildings: BuildingsProjectConfig = field(default_factory=BuildingsProjectConfig)
    materials: MaterialsProjectConfig = field(default_factory=MaterialsProjectConfig)
    export: ExportProjectConfig = field(default_factory=ExportProjectConfig)
    pipeline: PipelineProjectConfig = field(default_factory=PipelineProjectConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ProjectConfig:
        """Build a typed ProjectConfig from an untyped mapping."""

        default_terrain = TerrainProjectConfig()
        default_roads = RoadsProjectConfig()
        default_buildings = BuildingsProjectConfig()
        default_materials = MaterialsProjectConfig()
        default_export = ExportProjectConfig()
        default_pipeline = PipelineProjectConfig()

        terrain_data = data.get("terrain", {})
        roads_data = data.get("roads", {})
        buildings_data = data.get("buildings", {})
        materials_data = data.get("materials", {})
        export_data = data.get("export", {})
        pipeline_data = data.get("pipeline", {})

        return cls(
            terrain=TerrainProjectConfig(
                page_size=int(terrain_data.get("page_size", default_terrain.page_size)),
                output_size=tuple(terrain_data.get("output_size", default_terrain.output_size)),
                colormap=str(terrain_data.get("colormap", default_terrain.colormap)),
                smoothing_sigma=float(
                    terrain_data.get("smoothing_sigma", default_terrain.smoothing_sigma)
                ),
            ),
            roads=RoadsProjectConfig(
                network_type=str(roads_data.get("network_type", default_roads.network_type)),
                simplify=bool(roads_data.get("simplify", default_roads.simplify)),
                default_width=float(roads_data.get("default_width", default_roads.default_width)),
                default_border_width=float(
                    roads_data.get("default_border_width", default_roads.default_border_width)
                ),
                default_border_height=float(
                    roads_data.get("default_border_height", default_roads.default_border_height)
                ),
            ),
            buildings=BuildingsProjectConfig(
                enabled=bool(buildings_data.get("enabled", default_buildings.enabled)),
            ),
            materials=MaterialsProjectConfig(
                default_ground_texture=str(
                    materials_data.get(
                        "default_ground_texture",
                        default_materials.default_ground_texture,
                    )
                ),
            ),
            export=ExportProjectConfig(
                output_name=str(export_data.get("output_name", default_export.output_name)),
                include_roads=bool(export_data.get("include_roads", default_export.include_roads)),
                include_buildings=bool(
                    export_data.get("include_buildings", default_export.include_buildings)
                ),
            ),
            pipeline=PipelineProjectConfig(
                preload_elevation=bool(
                    pipeline_data.get("preload_elevation", default_pipeline.preload_elevation)
                ),
            ),
        )
