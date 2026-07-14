# -*- coding: utf-8 -*-
"""
OSM2terrn CLI launcher.
"""
from __future__ import annotations

import argparse
from dotenv import load_dotenv
import os
import sys
from typing import Any

from osm2terrn.config.settings import configure, get_project_loader

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="osm2terrn",
        description="OSM2terrn interactive CLI",
    )
    parser.add_argument("--project-dir", type=str, default=None)
    parser.add_argument("--config-file", type=str, default=None)

    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--logs-dir", type=str, default=None)
    parser.add_argument("--cache-dir", type=str, default=None)

    parser.add_argument("--terrain-page-size", type=int, default=None)
    parser.add_argument("--terrain-output-width", type=int, default=None)
    parser.add_argument("--terrain-output-height", type=int, default=None)
    parser.add_argument("--terrain-colormap", type=str, default=None)
    parser.add_argument("--terrain-smoothing-sigma", type=float, default=None)

    parser.add_argument("--roads-network-type", type=str, default=None)
    parser.add_argument("--roads-simplify", action="store_true")
    parser.add_argument("--roads-no-simplify", action="store_true")
    parser.add_argument("--roads-default-width", type=float, default=None)
    parser.add_argument("--roads-default-border-width", type=float, default=None)
    parser.add_argument("--roads-default-border-height", type=float, default=None)

    parser.add_argument("--buildings-enabled", action="store_true")
    parser.add_argument("--buildings-disabled", action="store_true")

    parser.add_argument("--materials-default-ground-texture", type=str, default=None)

    parser.add_argument("--export-output-name", type=str, default=None)
    parser.add_argument("--export-include-roads", action="store_true")
    parser.add_argument("--export-no-include-roads", action="store_true")
    parser.add_argument("--export-include-buildings", action="store_true")
    parser.add_argument("--export-no-include-buildings", action="store_true")

    parser.add_argument("--pipeline-preload-elevation", action="store_true")
    parser.add_argument("--pipeline-no-preload-elevation", action="store_true")

    return parser


def _build_program_cli_overrides(args: argparse.Namespace) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    if args.output_dir is not None:
        paths["output_dir"] = args.output_dir
    if args.logs_dir is not None:
        paths["logs_dir"] = args.logs_dir
    if args.cache_dir is not None:
        paths["cache_dir"] = args.cache_dir
    return {"paths": paths} if paths else {}


def _build_project_cli_overrides(args: argparse.Namespace) -> dict[str, Any]:
    overrides: dict[str, Any] = {}

    terrain: dict[str, Any] = {}
    if args.terrain_page_size is not None:
        terrain["page_size"] = args.terrain_page_size
    if args.terrain_output_width is not None or args.terrain_output_height is not None:
        if args.terrain_output_width is None or args.terrain_output_height is None:
            raise ValueError("Both --terrain-output-width and --terrain-output-height are required together.")
        terrain["output_size"] = [args.terrain_output_width, args.terrain_output_height]
    if args.terrain_colormap is not None:
        terrain["colormap"] = args.terrain_colormap
    if args.terrain_smoothing_sigma is not None:
        terrain["smoothing_sigma"] = args.terrain_smoothing_sigma
    if terrain:
        overrides["terrain"] = terrain

    roads: dict[str, Any] = {}
    if args.roads_network_type is not None:
        roads["network_type"] = args.roads_network_type
    if args.roads_simplify and args.roads_no_simplify:
        raise ValueError("Use only one of --roads-simplify or --roads-no-simplify.")
    if args.roads_simplify:
        roads["simplify"] = True
    if args.roads_no_simplify:
        roads["simplify"] = False
    if args.roads_default_width is not None:
        roads["default_width"] = args.roads_default_width
    if args.roads_default_border_width is not None:
        roads["default_border_width"] = args.roads_default_border_width
    if args.roads_default_border_height is not None:
        roads["default_border_height"] = args.roads_default_border_height
    if roads:
        overrides["roads"] = roads

    buildings: dict[str, Any] = {}
    if args.buildings_enabled and args.buildings_disabled:
        raise ValueError("Use only one of --buildings-enabled or --buildings-disabled.")
    if args.buildings_enabled:
        buildings["enabled"] = True
    if args.buildings_disabled:
        buildings["enabled"] = False
    if buildings:
        overrides["buildings"] = buildings

    if args.materials_default_ground_texture is not None:
        overrides["materials"] = {
            "default_ground_texture": args.materials_default_ground_texture,
        }

    export: dict[str, Any] = {}
    if args.export_output_name is not None:
        export["output_name"] = args.export_output_name
    if args.export_include_roads and args.export_no_include_roads:
        raise ValueError("Use only one of --export-include-roads or --export-no-include-roads.")
    if args.export_include_roads:
        export["include_roads"] = True
    if args.export_no_include_roads:
        export["include_roads"] = False
    if args.export_include_buildings and args.export_no_include_buildings:
        raise ValueError("Use only one of --export-include-buildings or --export-no-include-buildings.")
    if args.export_include_buildings:
        export["include_buildings"] = True
    if args.export_no_include_buildings:
        export["include_buildings"] = False
    if export:
        overrides["export"] = export

    pipeline: dict[str, Any] = {}
    if args.pipeline_preload_elevation and args.pipeline_no_preload_elevation:
        raise ValueError(
            "Use only one of --pipeline-preload-elevation or --pipeline-no-preload-elevation."
        )
    if args.pipeline_preload_elevation:
        pipeline["preload_elevation"] = True
    if args.pipeline_no_preload_elevation:
        pipeline["preload_elevation"] = False
    if pipeline:
        overrides["pipeline"] = pipeline

    return overrides


def main(argv: list[str] | None = None) -> int:
    """Application entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    loader = get_project_loader()
    project_dir = args.project_dir or os.getenv("OSM2TERRN_PROJECT_DIR")

    try:
        program_cli_overrides = _build_program_cli_overrides(args)
        project_cli_overrides = _build_project_cli_overrides(args)
    except ValueError as exc:
        parser.error(str(exc))

    program_config = loader.load_program_config(cli_overrides=program_cli_overrides)
    project_config = loader.load_project_config(
        project_root=project_dir,
        config_file=args.config_file,
        cli_overrides=project_cli_overrides,
    )
    configure(program_config=program_config, project_config=project_config)

    from osm2terrn.cli.menu import mainmenu

    mainmenu.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
