from __future__ import annotations

import os

from pyproj import Transformer
from rich.console import Console

from osm2terrn.app.app_state import current_map
from osm2terrn.config.settings import get_project_config
from osm2terrn.data import osm_data_handler
from osm2terrn.data.osm_data_handler import download_data_from_bbox
from osm2terrn.domain.adapters.bounds import require_domain_bounding_box
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.processing import orchestrator
from osm2terrn.processing.terrain.heightmap_handler import fetch_elevation_from_api as heightmapper
from osm2terrn.utils.geometry.bounds import compute_world_params, make_square_bounds_centered
from osm2terrn.utils.logger import get_logger, log_info, log_warning


logger = get_logger("cli_commands")
console = Console()
_PROJECT_CONFIG = get_project_config()
download_menu = getattr(osm_data_handler, "download_menu")
export_terrain_assets = getattr(orchestrator, "export_terrain_assets")


def _bounds_center_lonlat(bounds: BoundingBox) -> tuple[float, float]:
    """Return the bounds center in longitude and latitude."""
    if bounds.crs is None or bounds.crs == "EPSG:4326":
        return (
            (bounds.min_x + bounds.max_x) / 2.0,
            (bounds.min_y + bounds.max_y) / 2.0,
        )

    transformer = Transformer.from_crs(bounds.crs, "EPSG:4326", always_xy=True)
    corners = (
        (bounds.min_x, bounds.min_y),
        (bounds.min_x, bounds.max_y),
        (bounds.max_x, bounds.min_y),
        (bounds.max_x, bounds.max_y),
    )
    transformed = [transformer.transform(x, y) for x, y in corners]
    longitudes = [float(point[0]) for point in transformed]
    latitudes = [float(point[1]) for point in transformed]
    return (
        (min(longitudes) + max(longitudes)) / 2.0,
        (min(latitudes) + max(latitudes)) / 2.0,
    )


def dlcity() -> None:
    """Download OSM data for a selected area and preload elevation for that extent."""
    clear()
    console.print("[bold cyan]Download map data[/bold cyan]", justify="center")
    console.print()

    place, bbox = download_menu()
    if not place or not bbox:
        console.print("[yellow]No place or bounding box selected. Returning to main menu.[/yellow]")
        return

    console.print(f"[cyan]Processing data for: [bold]{place}[/bold][/cyan]")

    data = download_data_from_bbox(bbox)
    downloaded_bounds = data.get("bounds")
    if downloaded_bounds is None:
        console.print("[red]Error: No bounds data available from bounding box.[/red]")
        current_map.data = {}
        current_map.elevation_data = {}
        current_map.terrain_world_size = None
        return

    try:
        domain_bounds = require_domain_bounding_box(downloaded_bounds)
        origin_lon, origin_lat = _bounds_center_lonlat(domain_bounds)
    except Exception as exc:
        log_warning(logger, f"Could not determine geographic origin from downloaded bounds: {exc}")
        origin_lon, origin_lat = 0.0, 0.0

    os.environ["OSM2TERRN_PLACE_NAME"] = place
    os.environ["OSM2TERRN_ORIGIN_LON"] = str(origin_lon)
    os.environ["OSM2TERRN_ORIGIN_LAT"] = str(origin_lat)

    current_map.terrain_world_size = None
    try:
        domain_bounds = require_domain_bounding_box(downloaded_bounds)
        world_size, _ = compute_world_params(
            domain_bounds,
            page_size=_PROJECT_CONFIG.terrain.page_size,
            snap_to_pow2=True,
        )
        data["bounds"] = make_square_bounds_centered(domain_bounds, world_size)
        current_map.terrain_world_size = world_size
    except Exception as exc:
        log_warning(logger, f"Could not square bounds: {exc}")
        data["bounds"] = downloaded_bounds

    current_map.data = data
    current_map.place = place
    current_map.origin_lon = origin_lon
    current_map.origin_lat = origin_lat

    try:
        console.print("[cyan]Fetching elevation data...[/cyan]")
        elevation, maxh, minh = heightmapper(data["bounds"])
        current_map.elevation_data = {"elevation": elevation, "maxh": maxh, "minh": minh}
        log_info(logger, "Elevation data loaded successfully.")
        console.print("[green]✓ Elevation data loaded successfully[/green]")
    except Exception as exc:
        log_warning(logger, f"Elevation preload failed: {exc}")
        current_map.elevation_data = {}
        console.print(f"[yellow]⚠ Elevation preload failed: {exc}[/yellow]")


def load() -> None:
    """Placeholder for loading/importing previously downloaded project data."""
    clear()
    console.print("[bold yellow]Loading project data...[/bold yellow]", justify="center")
    console.print()
    console.print("[dim]Loading functionality coming soon[/dim]")


def export() -> None:
    """Export current map data to terrain assets."""
    clear()
    console.print("[bold cyan]Export terrain assets[/bold cyan]", justify="center")
    console.print()

    if not current_map.has_data():
        console.print("[red]No map data available. Please download a city first.[/red]")
        return

    try:
        console.print("[cyan]Exporting terrain assets...[/cyan]")
        output_files = export_terrain_assets(
            place=current_map.place,
            bounds=current_map.data["bounds"],
            elevation_data=current_map.elevation_data,
            origin_lon=current_map.origin_lon,
            origin_lat=current_map.origin_lat,
            target_bounds=current_map.data.get("bounds"),
            road_network=current_map.data.get("roads"),
            acquisition_results=current_map.data.get("acquisition_results"),
            terrain_world_size=current_map.terrain_world_size,
        )
        roads_outcome = output_files.get("roads_outcome")
        export_outcome = output_files.get("export_outcome")
        if export_outcome is None:
            export_outcome = "partial" if roads_outcome in {"failed", "not_requested"} else "complete"

        partial_reasons = output_files.get("partial_reasons")
        acquisition_warnings = output_files.get("acquisition_warnings")
        if export_outcome == "partial":
            reason = partial_reasons or "one or more requested export stages did not complete"
            log_warning(logger, f"Partial export: {reason}.")
            console.print(f"[yellow]⚠ Partial export: {reason}.[/yellow]")
        elif acquisition_warnings:
            log_warning(logger, f"Export completed with acquisition warnings: {acquisition_warnings}.")
            console.print(f"[yellow]⚠ Export complete with acquisition warnings: {acquisition_warnings}[/yellow]")
        else:
            console.print("[green]✓ Export complete:[/green]")

        non_file_keys = {
            "roads_outcome",
            "buildings_outcome",
            "elevation_outcome",
            "export_outcome",
            "partial_reasons",
            "acquisition_warnings",
        }
        for label, path in output_files.items():
            if label not in non_file_keys and path:
                console.print(f"  [green]✓[/green] {label}: [cyan]{path}[/cyan]")
    except Exception as exc:
        console.print(f"[red]Error during export: {exc}[/red]")


def exit_program() -> None:
    """Terminate the CLI session."""
    console.print("[bold yellow]Exiting OSM2terrn...[/bold yellow]")
    raise SystemExit(0)


def clear() -> None:
    """Clear terminal output using the platform-appropriate command."""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
