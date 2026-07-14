"""Configuration loader entrypoint for program and project config."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from osm2terrn.config.defaults import build_default_program_config, build_default_project_config
from osm2terrn.config.models import ProgramConfig, ProjectConfig
from osm2terrn.config.validator import validate_program_config, validate_project_config


class ProjectLoader:
    """Single entrypoint responsible for locating, reading and validating config."""

    # YAML is preferred: it is less verbose and hierarchical.
    # TOML and JSON are supported for compatibility.
    PROJECT_FILE_CANDIDATES = (
        "project.yaml",
        "project.yml",
        "project.toml",
        "project.json",
    )

    # Lower to higher priority. Later layers override earlier ones.
    PRECEDENCE_ORDER = (
        "defaults",
        "project_files",
        "cli",
        "interface",
    )

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root

    def load_program_config(
        self,
        overrides: Mapping[str, Any] | None = None,
        cli_overrides: Mapping[str, Any] | None = None,
        interface_overrides: Mapping[str, Any] | None = None,
    ) -> ProgramConfig:
        """Load typed internal program configuration with explicit precedence layers."""

        config = build_default_program_config(self.workspace_root)
        merged = self._apply_precedence_layers(
            self._program_config_to_mapping(config),
            [
                overrides,
                cli_overrides,
                interface_overrides,
            ],
        )
        hydrated = self._hydrate_program_config(merged)
        return validate_program_config(hydrated)

    def load_project_config(
        self,
        project_root: str | Path | None = None,
        config_file: str | Path | None = None,
        overrides: Mapping[str, Any] | None = None,
        cli_overrides: Mapping[str, Any] | None = None,
        interface_overrides: Mapping[str, Any] | None = None,
    ) -> ProjectConfig:
        """Load typed project generation configuration with explicit precedence layers.

        Applied order (lower -> higher priority):
        1) defaults
        2) project file(s), including include/includes expansions
        3) CLI overrides
        4) interface/API overrides

        Backward compatibility:
        - `overrides` is preserved and applied as a legacy layer before `cli_overrides`.
        """

        defaults = build_default_project_config()
        merged_data: dict[str, Any] = self._project_config_to_mapping(defaults)

        resolved_file = self._resolve_project_file(project_root=project_root, config_file=config_file)
        project_file_data: dict[str, Any] = {}
        if resolved_file is not None:
            project_file_data = self._read_config_file(resolved_file)

        merged_data = self._apply_precedence_layers(
            merged_data,
            [
                project_file_data,
                overrides,
                cli_overrides,
                interface_overrides,
            ],
        )

        project = ProjectConfig.from_mapping(merged_data)
        return validate_project_config(project)

    def _resolve_project_file(
        self,
        project_root: str | Path | None,
        config_file: str | Path | None,
    ) -> Path | None:
        if config_file is not None:
            path = Path(config_file)
            return path if path.exists() else None

        if project_root is None:
            return None

        root = Path(project_root)
        if not root.exists() or not root.is_dir():
            return None

        for filename in self.PROJECT_FILE_CANDIDATES:
            candidate = root / filename
            if candidate.exists():
                return candidate

        return None

    def _read_config_file(
        self,
        file_path: Path,
        visited: set[Path] | None = None,
    ) -> dict[str, Any]:
        resolved_file = file_path.resolve()
        chain = visited or set()
        if resolved_file in chain:
            raise ValueError(f"Circular config include detected: {resolved_file}")

        chain.add(resolved_file)
        raw = self._read_raw_config_file(resolved_file)

        includes: Sequence[str] = []
        include_value = raw.get("include")
        includes_value = raw.get("includes")
        if isinstance(include_value, str):
            includes = [include_value]
        elif isinstance(include_value, Sequence) and not isinstance(include_value, (str, bytes)):
            includes = [str(item) for item in include_value]

        if isinstance(includes_value, str):
            includes = [*includes, includes_value]
        elif isinstance(includes_value, Sequence) and not isinstance(includes_value, (str, bytes)):
            includes = [*includes, *[str(item) for item in includes_value]]

        merged_includes: dict[str, Any] = {}
        for include in includes:
            include_path = (resolved_file.parent / include).resolve()
            if not include_path.exists():
                raise ValueError(f"Included config file not found: {include_path}")
            included_data = self._read_config_file(include_path, visited=chain)
            merged_includes = self._merge_mapping(merged_includes, included_data)

        current_data = dict(raw)
        current_data.pop("include", None)
        current_data.pop("includes", None)

        chain.remove(resolved_file)
        return self._merge_mapping(merged_includes, current_data)

    def _read_raw_config_file(self, file_path: Path) -> dict[str, Any]:
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            return self._read_json(file_path)
        if suffix == ".toml":
            return self._read_toml(file_path)
        if suffix in {".yaml", ".yml"}:
            return self._read_yaml(file_path)
        raise ValueError(f"Unsupported config format: {suffix}")

    @classmethod
    def _apply_precedence_layers(
        cls,
        base: dict[str, Any],
        layers: Sequence[Mapping[str, Any] | None],
    ) -> dict[str, Any]:
        merged = dict(base)
        for layer in layers:
            if layer:
                merged = cls._merge_mapping(merged, dict(layer))
        return merged

    @staticmethod
    def _read_json(file_path: Path) -> dict[str, Any]:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"JSON config must be an object: {file_path}")
        return data

    @staticmethod
    def _read_toml(file_path: Path) -> dict[str, Any]:
        import tomllib

        with file_path.open("rb") as handle:
            data = tomllib.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"TOML config must be a table/object: {file_path}")
        return data

    @staticmethod
    def _read_yaml(file_path: Path) -> dict[str, Any]:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "YAML parsing requested but PyYAML is not installed. "
                "Install dependency 'pyyaml' to use YAML project configs."
            ) from exc

        with file_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML config must be a mapping/object: {file_path}")
        return data

    @classmethod
    def _merge_mapping(cls, base: dict[str, Any], updates: Mapping[str, Any]) -> dict[str, Any]:
        result = dict(base)
        for key, value in updates.items():
            base_value = result.get(key)
            if isinstance(base_value, dict) and isinstance(value, Mapping):
                result[key] = cls._merge_mapping(base_value, dict(value))
            else:
                result[key] = value
        return result

    @staticmethod
    def _program_config_to_mapping(config: ProgramConfig) -> dict[str, Any]:
        return {
            "paths": {
                "workspace_root": config.paths.workspace_root,
                "output_dir": config.paths.output_dir,
                "logs_dir": config.paths.logs_dir,
                "cache_dir": config.paths.cache_dir,
                "projects_dir": config.paths.projects_dir,
            },
            "logging": {
                "level": config.logging.level,
                "datefmt": config.logging.datefmt,
                "fmt": config.logging.fmt,
                "enable_console": config.logging.enable_console,
                "enable_file": config.logging.enable_file,
                "default_log_file": config.logging.default_log_file,
            },
            "cache": {
                "enabled": config.cache.enabled,
                "max_size_mb": config.cache.max_size_mb,
            },
            "providers": {
                "opentopo_api_key_env_var": config.providers.opentopo_api_key_env_var,
                "overpass_max_query_area_size_env_var": config.providers.overpass_max_query_area_size_env_var,
                "overpass_requests_timeout_env_var": config.providers.overpass_requests_timeout_env_var,
                "overpass_rate_limit_env_var": config.providers.overpass_rate_limit_env_var,
                "elevation_url_template": config.providers.elevation_url_template,
            },
            "osm": {
                "custom_tags": list(config.osm.custom_tags),
                "map_geometries": dict(config.osm.map_geometries),
                "networks": dict(config.osm.networks),
                "max_query_area_size": config.osm.max_query_area_size,
                "requests_timeout": config.osm.requests_timeout,
                "overpass_rate_limit": config.osm.overpass_rate_limit,
                "osmnx_log_console": config.osm.osmnx_log_console,
                "osmnx_log_file": config.osm.osmnx_log_file,
                "osmnx_log_level": config.osm.osmnx_log_level,
            },
            "terrain_runtime": {
                "output_size": list(config.terrain_runtime.output_size),
                "page_size": config.terrain_runtime.page_size,
                "default_colormap": config.terrain_runtime.default_colormap,
                "default_place_name": config.terrain_runtime.default_place_name,
                "default_tobj_prefix": config.terrain_runtime.default_tobj_prefix,
                "smoothing_sigma": config.terrain_runtime.smoothing_sigma,
                "default_output_subdir": config.terrain_runtime.default_output_subdir,
            },
            "water_runtime": {
                "sea_level": config.water_runtime.sea_level,
                "min_terrain_height_above_water": config.water_runtime.min_terrain_height_above_water,
                "water_elevation_percentile": config.water_runtime.water_elevation_percentile,
                "default_water_depth": config.water_runtime.default_water_depth,
                "enable_realistic_water": config.water_runtime.enable_realistic_water,
                "default_water_enabled": config.water_runtime.default_water_enabled,
                "default_water_line": config.water_runtime.default_water_line,
                "default_water_bottom_line": config.water_runtime.default_water_bottom_line,
            },
            "elevation_runtime": {
                "enable_realistic_elevation": config.elevation_runtime.enable_realistic_elevation,
                "default_world_size_y": config.elevation_runtime.default_world_size_y,
                "min_world_size_y": config.elevation_runtime.min_world_size_y,
                "max_world_size_y": config.elevation_runtime.max_world_size_y,
                "normalization_tolerance": config.elevation_runtime.normalization_tolerance,
            },
            "terrn2_runtime": {
                "default_ambient_color": config.terrn2_runtime.default_ambient_color,
                "default_sandstorm_cubemap": config.terrn2_runtime.default_sandstorm_cubemap,
                "default_start_position": config.terrn2_runtime.default_start_position,
                "default_start_rotation": config.terrn2_runtime.default_start_rotation,
                "default_gravity": config.terrn2_runtime.default_gravity,
                "default_category_id": config.terrn2_runtime.default_category_id,
                "default_version": config.terrn2_runtime.default_version,
            },
            "otc_runtime": {
                "default_world_size_y": config.otc_runtime.default_world_size_y,
                "default_page_size": config.otc_runtime.default_page_size,
                "layer_blend_map_size": config.otc_runtime.layer_blend_map_size,
                "min_batch_size": config.otc_runtime.min_batch_size,
                "max_batch_size": config.otc_runtime.max_batch_size,
                "disable_caching": config.otc_runtime.disable_caching,
                "default_base_layer_world_size": config.otc_runtime.default_base_layer_world_size,
                "default_groundmap_base_layer_world_size": config.otc_runtime.default_groundmap_base_layer_world_size,
                "default_layer_alpha": config.otc_runtime.default_layer_alpha,
                "default_detail_diffuse_texture": config.otc_runtime.default_detail_diffuse_texture,
                "default_normal_texture": config.otc_runtime.default_normal_texture,
                "legacy_cell_size": config.otc_runtime.legacy_cell_size,
                "legacy_texture_repeat": config.otc_runtime.legacy_texture_repeat,
            },
        }

    @staticmethod
    def _project_config_to_mapping(config: ProjectConfig) -> dict[str, Any]:
        return {
            "terrain": {
                "page_size": config.terrain.page_size,
                "output_size": list(config.terrain.output_size),
                "colormap": config.terrain.colormap,
                "smoothing_sigma": config.terrain.smoothing_sigma,
            },
            "roads": {
                "network_type": config.roads.network_type,
                "simplify": config.roads.simplify,
                "default_width": config.roads.default_width,
                "default_border_width": config.roads.default_border_width,
                "default_border_height": config.roads.default_border_height,
            },
            "buildings": {
                "enabled": config.buildings.enabled,
            },
            "materials": {
                "default_ground_texture": config.materials.default_ground_texture,
            },
            "export": {
                "output_name": config.export.output_name,
                "include_roads": config.export.include_roads,
                "include_buildings": config.export.include_buildings,
            },
            "pipeline": {
                "preload_elevation": config.pipeline.preload_elevation,
            },
        }

    @staticmethod
    def _hydrate_program_config(data: Mapping[str, Any]) -> ProgramConfig:
        paths_data = data.get("paths", {})
        logging_data = data.get("logging", {})
        cache_data = data.get("cache", {})
        providers_data = data.get("providers", {})
        osm_data = data.get("osm", {})
        terrain_runtime_data = data.get("terrain_runtime", {})
        water_runtime_data = data.get("water_runtime", {})
        elevation_runtime_data = data.get("elevation_runtime", {})
        terrn2_runtime_data = data.get("terrn2_runtime", {})
        otc_runtime_data = data.get("otc_runtime", {})

        defaults = build_default_program_config()

        paths = defaults.paths
        workspace_root = Path(paths_data.get("workspace_root", paths.workspace_root))
        output_dir = Path(paths_data.get("output_dir", paths.output_dir))
        logs_dir = Path(paths_data.get("logs_dir", paths.logs_dir))
        cache_dir = Path(paths_data.get("cache_dir", paths.cache_dir))
        projects_dir = Path(paths_data.get("projects_dir", paths.projects_dir))

        from osm2terrn.config.models import (
            CacheConfig,
            ElevationRuntimeConfig,
            LoggingConfig,
            OsmConfig,
            OtcRuntimeConfig,
            PathConfig,
            ProgramConfig,
            ProviderConfig,
            Terrn2RuntimeConfig,
            TerrainRuntimeConfig,
            WaterRuntimeConfig,
        )

        providers = ProviderConfig(
            opentopo_api_key_env_var=str(
                providers_data.get(
                    "opentopo_api_key_env_var",
                    defaults.providers.opentopo_api_key_env_var,
                )
            ),
            overpass_max_query_area_size_env_var=str(
                providers_data.get(
                    "overpass_max_query_area_size_env_var",
                    defaults.providers.overpass_max_query_area_size_env_var,
                )
            ),
            overpass_requests_timeout_env_var=str(
                providers_data.get(
                    "overpass_requests_timeout_env_var",
                    defaults.providers.overpass_requests_timeout_env_var,
                )
            ),
            overpass_rate_limit_env_var=str(
                providers_data.get(
                    "overpass_rate_limit_env_var",
                    defaults.providers.overpass_rate_limit_env_var,
                )
            ),
            elevation_url_template=str(
                providers_data.get("elevation_url_template", defaults.providers.elevation_url_template)
            ),
        )

        max_query_area_size = int(
            os.getenv(
                providers.overpass_max_query_area_size_env_var,
                osm_data.get("max_query_area_size", defaults.osm.max_query_area_size),
            )
        )
        requests_timeout = int(
            os.getenv(
                providers.overpass_requests_timeout_env_var,
                osm_data.get("requests_timeout", defaults.osm.requests_timeout),
            )
        )
        overpass_rate_limit = bool(
            os.getenv(
                providers.overpass_rate_limit_env_var,
                osm_data.get("overpass_rate_limit", defaults.osm.overpass_rate_limit),
            )
        )

        return ProgramConfig(
            paths=PathConfig(
                workspace_root=workspace_root,
                output_dir=output_dir,
                logs_dir=logs_dir,
                cache_dir=cache_dir,
                projects_dir=projects_dir,
            ),
            logging=LoggingConfig(
                level=int(logging_data.get("level", defaults.logging.level)),
                datefmt=str(logging_data.get("datefmt", defaults.logging.datefmt)),
                fmt=str(logging_data.get("fmt", defaults.logging.fmt)),
                enable_console=bool(
                    logging_data.get("enable_console", defaults.logging.enable_console)
                ),
                enable_file=bool(logging_data.get("enable_file", defaults.logging.enable_file)),
                default_log_file=Path(
                    logging_data.get("default_log_file", defaults.logging.default_log_file)
                )
                if logging_data.get("default_log_file", defaults.logging.default_log_file)
                else None,
            ),
            cache=CacheConfig(
                enabled=bool(cache_data.get("enabled", defaults.cache.enabled)),
                max_size_mb=int(cache_data.get("max_size_mb", defaults.cache.max_size_mb)),
            ),
            providers=providers,
            osm=OsmConfig(
                custom_tags=tuple(osm_data.get("custom_tags", defaults.osm.custom_tags)),
                map_geometries=dict(osm_data.get("map_geometries", defaults.osm.map_geometries)),
                networks=dict(osm_data.get("networks", defaults.osm.networks)),
                max_query_area_size=max_query_area_size,
                requests_timeout=requests_timeout,
                overpass_rate_limit=overpass_rate_limit,
                osmnx_log_console=bool(
                    osm_data.get("osmnx_log_console", defaults.osm.osmnx_log_console)
                ),
                osmnx_log_file=bool(osm_data.get("osmnx_log_file", defaults.osm.osmnx_log_file)),
                osmnx_log_level=int(osm_data.get("osmnx_log_level", defaults.osm.osmnx_log_level)),
            ),
            terrain_runtime=TerrainRuntimeConfig(
                output_size=tuple(
                    terrain_runtime_data.get("output_size", defaults.terrain_runtime.output_size)
                ),
                page_size=int(
                    terrain_runtime_data.get("page_size", defaults.terrain_runtime.page_size)
                ),
                default_colormap=str(
                    terrain_runtime_data.get(
                        "default_colormap", defaults.terrain_runtime.default_colormap
                    )
                ),
                default_place_name=str(
                    terrain_runtime_data.get(
                        "default_place_name", defaults.terrain_runtime.default_place_name
                    )
                ),
                default_tobj_prefix=str(
                    terrain_runtime_data.get(
                        "default_tobj_prefix", defaults.terrain_runtime.default_tobj_prefix
                    )
                ),
                smoothing_sigma=float(
                    terrain_runtime_data.get(
                        "smoothing_sigma", defaults.terrain_runtime.smoothing_sigma
                    )
                ),
                default_output_subdir=str(
                    terrain_runtime_data.get(
                        "default_output_subdir", defaults.terrain_runtime.default_output_subdir
                    )
                ),
            ),
            water_runtime=WaterRuntimeConfig(
                sea_level=float(
                    water_runtime_data.get("sea_level", defaults.water_runtime.sea_level)
                ),
                min_terrain_height_above_water=float(
                    water_runtime_data.get(
                        "min_terrain_height_above_water",
                        defaults.water_runtime.min_terrain_height_above_water,
                    )
                ),
                water_elevation_percentile=int(
                    water_runtime_data.get(
                        "water_elevation_percentile",
                        defaults.water_runtime.water_elevation_percentile,
                    )
                ),
                default_water_depth=float(
                    water_runtime_data.get(
                        "default_water_depth", defaults.water_runtime.default_water_depth
                    )
                ),
                enable_realistic_water=bool(
                    water_runtime_data.get(
                        "enable_realistic_water", defaults.water_runtime.enable_realistic_water
                    )
                ),
                default_water_enabled=int(
                    water_runtime_data.get(
                        "default_water_enabled", defaults.water_runtime.default_water_enabled
                    )
                ),
                default_water_line=float(
                    water_runtime_data.get(
                        "default_water_line", defaults.water_runtime.default_water_line
                    )
                ),
                default_water_bottom_line=float(
                    water_runtime_data.get(
                        "default_water_bottom_line",
                        defaults.water_runtime.default_water_bottom_line,
                    )
                ),
            ),
            elevation_runtime=ElevationRuntimeConfig(
                enable_realistic_elevation=bool(
                    elevation_runtime_data.get(
                        "enable_realistic_elevation",
                        defaults.elevation_runtime.enable_realistic_elevation,
                    )
                ),
                default_world_size_y=float(
                    elevation_runtime_data.get(
                        "default_world_size_y", defaults.elevation_runtime.default_world_size_y
                    )
                ),
                min_world_size_y=float(
                    elevation_runtime_data.get(
                        "min_world_size_y", defaults.elevation_runtime.min_world_size_y
                    )
                ),
                max_world_size_y=float(
                    elevation_runtime_data.get(
                        "max_world_size_y", defaults.elevation_runtime.max_world_size_y
                    )
                ),
                normalization_tolerance=float(
                    elevation_runtime_data.get(
                        "normalization_tolerance",
                        defaults.elevation_runtime.normalization_tolerance,
                    )
                ),
            ),
            terrn2_runtime=Terrn2RuntimeConfig(
                default_ambient_color=str(
                    terrn2_runtime_data.get(
                        "default_ambient_color", defaults.terrn2_runtime.default_ambient_color
                    )
                ),
                default_sandstorm_cubemap=str(
                    terrn2_runtime_data.get(
                        "default_sandstorm_cubemap",
                        defaults.terrn2_runtime.default_sandstorm_cubemap,
                    )
                ),
                default_start_position=str(
                    terrn2_runtime_data.get(
                        "default_start_position", defaults.terrn2_runtime.default_start_position
                    )
                ),
                default_start_rotation=float(
                    terrn2_runtime_data.get(
                        "default_start_rotation", defaults.terrn2_runtime.default_start_rotation
                    )
                ),
                default_gravity=float(
                    terrn2_runtime_data.get(
                        "default_gravity", defaults.terrn2_runtime.default_gravity
                    )
                ),
                default_category_id=int(
                    terrn2_runtime_data.get(
                        "default_category_id", defaults.terrn2_runtime.default_category_id
                    )
                ),
                default_version=int(
                    terrn2_runtime_data.get(
                        "default_version", defaults.terrn2_runtime.default_version
                    )
                ),
            ),
            otc_runtime=OtcRuntimeConfig(
                default_world_size_y=float(
                    otc_runtime_data.get(
                        "default_world_size_y", defaults.otc_runtime.default_world_size_y
                    )
                ),
                default_page_size=int(
                    otc_runtime_data.get(
                        "default_page_size", defaults.otc_runtime.default_page_size
                    )
                ),
                layer_blend_map_size=int(
                    otc_runtime_data.get(
                        "layer_blend_map_size", defaults.otc_runtime.layer_blend_map_size
                    )
                ),
                min_batch_size=int(
                    otc_runtime_data.get(
                        "min_batch_size", defaults.otc_runtime.min_batch_size
                    )
                ),
                max_batch_size=int(
                    otc_runtime_data.get(
                        "max_batch_size", defaults.otc_runtime.max_batch_size
                    )
                ),
                disable_caching=bool(
                    otc_runtime_data.get(
                        "disable_caching", defaults.otc_runtime.disable_caching
                    )
                ),
                default_base_layer_world_size=int(
                    otc_runtime_data.get(
                        "default_base_layer_world_size",
                        defaults.otc_runtime.default_base_layer_world_size,
                    )
                ),
                default_groundmap_base_layer_world_size=int(
                    otc_runtime_data.get(
                        "default_groundmap_base_layer_world_size",
                        defaults.otc_runtime.default_groundmap_base_layer_world_size,
                    )
                ),
                default_layer_alpha=float(
                    otc_runtime_data.get(
                        "default_layer_alpha", defaults.otc_runtime.default_layer_alpha
                    )
                ),
                default_detail_diffuse_texture=str(
                    otc_runtime_data.get(
                        "default_detail_diffuse_texture",
                        defaults.otc_runtime.default_detail_diffuse_texture,
                    )
                ),
                default_normal_texture=str(
                    otc_runtime_data.get(
                        "default_normal_texture",
                        defaults.otc_runtime.default_normal_texture,
                    )
                ),
                legacy_cell_size=float(
                    otc_runtime_data.get(
                        "legacy_cell_size",
                        defaults.otc_runtime.legacy_cell_size,
                    )
                ),
                legacy_texture_repeat=float(
                    otc_runtime_data.get(
                        "legacy_texture_repeat",
                        defaults.otc_runtime.legacy_texture_repeat,
                    )
                ),
            ),
        )
