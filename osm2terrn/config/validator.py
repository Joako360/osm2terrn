"""Validation logic for typed configuration models."""

from __future__ import annotations

from pathlib import Path

from osm2terrn.config.models import ProgramConfig, ProjectConfig


class ConfigurationError(ValueError):
    """Raised when configuration validation fails."""


def _ensure_positive_int(value: int, name: str) -> None:
    if value <= 0:
        raise ConfigurationError(f"{name} must be > 0. Received: {value}")


def _ensure_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ConfigurationError(f"{name} must be >= 0. Received: {value}")


def validate_program_config(config: ProgramConfig) -> ProgramConfig:
    """Validate internal program configuration values."""

    _ensure_positive_int(config.cache.max_size_mb, "cache.max_size_mb")
    _ensure_positive_int(config.osm.max_query_area_size, "osm.max_query_area_size")
    _ensure_positive_int(config.osm.requests_timeout, "osm.requests_timeout")
    _ensure_positive_int(config.terrain_runtime.page_size, "terrain_runtime.page_size")
    _ensure_positive_int(config.otc_runtime.default_page_size, "otc_runtime.default_page_size")
    _ensure_positive_int(
        int(config.otc_runtime.default_base_layer_world_size),
        "otc_runtime.default_base_layer_world_size",
    )
    _ensure_positive_int(
        int(config.otc_runtime.default_groundmap_base_layer_world_size),
        "otc_runtime.default_groundmap_base_layer_world_size",
    )
    _ensure_positive_int(config.elevation_runtime.min_world_size_y, "elevation_runtime.min_world_size_y")
    _ensure_positive_int(config.elevation_runtime.max_world_size_y, "elevation_runtime.max_world_size_y")
    if config.elevation_runtime.min_world_size_y > config.elevation_runtime.max_world_size_y:
        raise ConfigurationError(
            "elevation_runtime.min_world_size_y cannot be greater than "
            "elevation_runtime.max_world_size_y"
        )
    _ensure_non_negative(config.water_runtime.default_water_depth, "water_runtime.default_water_depth")
    _ensure_non_negative(config.elevation_runtime.normalization_tolerance, "elevation_runtime.normalization_tolerance")
    _ensure_non_negative(config.otc_runtime.legacy_cell_size, "otc_runtime.legacy_cell_size")
    _ensure_non_negative(config.otc_runtime.legacy_texture_repeat, "otc_runtime.legacy_texture_repeat")

    for path_name, path_value in (
        ("paths.workspace_root", config.paths.workspace_root),
        ("paths.output_dir", config.paths.output_dir),
        ("paths.logs_dir", config.paths.logs_dir),
        ("paths.cache_dir", config.paths.cache_dir),
        ("paths.projects_dir", config.paths.projects_dir),
    ):
        if not isinstance(path_value, Path):
            raise ConfigurationError(f"{path_name} must be pathlib.Path")

    return config


def validate_project_config(config: ProjectConfig) -> ProjectConfig:
    """Validate project-specific configuration values."""

    _ensure_positive_int(config.terrain.page_size, "project.terrain.page_size")

    if len(config.terrain.output_size) != 2:
        raise ConfigurationError("project.terrain.output_size must contain exactly two integers")

    output_w, output_h = config.terrain.output_size
    _ensure_positive_int(int(output_w), "project.terrain.output_size[0]")
    _ensure_positive_int(int(output_h), "project.terrain.output_size[1]")

    _ensure_non_negative(config.terrain.smoothing_sigma, "project.terrain.smoothing_sigma")
    _ensure_non_negative(config.roads.default_width, "project.roads.default_width")
    _ensure_non_negative(config.roads.default_border_width, "project.roads.default_border_width")
    _ensure_non_negative(config.roads.default_border_height, "project.roads.default_border_height")

    return config
