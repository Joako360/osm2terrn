"""Default typed configuration objects for osm2terrn."""

from __future__ import annotations

import logging
from pathlib import Path

from osm2terrn.config.models import (
    CacheConfig,
    ElevationRuntimeConfig,
    LoggingConfig,
    OsmConfig,
    OtcRuntimeConfig,
    PathConfig,
    PipelineProjectConfig,
    ProgramConfig,
    ProjectConfig,
    ProviderConfig,
    Terrn2RuntimeConfig,
    TerrainProjectConfig,
    TerrainRuntimeConfig,
    WaterRuntimeConfig,
)
from osm2terrn.config.paths import (
    default_cache_dir,
    default_logs_dir,
    default_output_dir,
    default_projects_dir,
    get_workspace_root,
)


def build_default_paths(workspace_root: Path | None = None) -> PathConfig:
    """Build default runtime paths for the current workspace."""

    root = workspace_root or get_workspace_root()
    return PathConfig(
        workspace_root=root,
        output_dir=default_output_dir(root),
        logs_dir=default_logs_dir(root),
        cache_dir=default_cache_dir(root),
        projects_dir=default_projects_dir(root),
    )


def build_default_program_config(workspace_root: Path | None = None) -> ProgramConfig:
    """Return default internal program configuration."""

    paths = build_default_paths(workspace_root)
    return ProgramConfig(
        paths=paths,
        logging=LoggingConfig(
            level=logging.INFO,
            enable_console=True,
            enable_file=False,
            default_log_file=paths.logs_dir / "osm2terrn.log",
        ),
        cache=CacheConfig(enabled=True, max_size_mb=512),
        providers=ProviderConfig(),
        osm=OsmConfig(
            custom_tags=(
                "aerialway",
                "aeroway",
                "cycleway",
                "footway",
                "railway",
                "waterway",
            ),
            map_geometries={
                "buildings": {
                    "amenity": "school",
                    "building": True,
                },
                "parks": {
                    "landuse": "grass",
                    "natural": "wood",
                    "leisure": "park",
                },
                "lakes": {
                    "natural": "water",
                    "water": ["lake", "river"],
                },
            },
            networks={
                "roads": None,
                "rails": "[\"railway\"~\"tram|rail\"]",
            },
        ),
        terrain_runtime=TerrainRuntimeConfig(),
        water_runtime=WaterRuntimeConfig(),
        elevation_runtime=ElevationRuntimeConfig(),
        terrn2_runtime=Terrn2RuntimeConfig(),
        otc_runtime=OtcRuntimeConfig(),
    )


def build_default_project_config() -> ProjectConfig:
    """Return default project generation configuration."""

    return ProjectConfig(
        terrain=TerrainProjectConfig(),
        pipeline=PipelineProjectConfig(preload_elevation=True),
    )
