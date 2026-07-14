from __future__ import annotations

import os

import geopandas as gpd
from shapely.geometry import box
from rich.console import Console

from osm2terrn.config.settings import get_project_config
from osm2terrn.app.app_state import current_map
from osm2terrn.data.osm_data_handler import download_data_from_bbox, download_menu
from osm2terrn.processing.terrain.heightmap_handler import fetch_elevation_from_api as heightmapper
from osm2terrn.domain.entities.bbox import BBox
from osm2terrn.utils.geometry.bounds import compute_world_params, make_square_bounds_centered
from osm2terrn.utils.logger import get_logger, log_info, log_warning
from osm2terrn.processing.orchestrator import export_terrain_assets

logger = get_logger("cli_commands")
console = Console()
_PROJECT_CONFIG = get_project_config()


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
    bounds_gdf = data.get("bounds")
    if bounds_gdf is None:
        console.print("[red]Error: No bounds data available from bounding box.[/red]")
        current_map.data = {}
        current_map.elevation_data = {}
        return

    try:
        bbox_obj = BBox(bbox)
        origin_lon = (bbox_obj.west + bbox_obj.east) / 2.0
        origin_lat = (bbox_obj.south + bbox_obj.north) / 2.0
    except Exception:
        try:
            centroid = bounds_gdf.to_crs(4326).geometry.centroid.iloc[0]
            origin_lon = float(centroid.x)
            origin_lat = float(centroid.y)
        except Exception:
            origin_lon, origin_lat = 0.0, 0.0

    os.environ["OSM2TERRN_PLACE_NAME"] = place
    os.environ["OSM2TERRN_ORIGIN_LON"] = str(origin_lon)
    os.environ["OSM2TERRN_ORIGIN_LAT"] = str(origin_lat)

    try:
        minx, miny, maxx, maxy = bounds_gdf.to_crs(4326).total_bounds
        page_size = _PROJECT_CONFIG.terrain.page_size
        initial_bounds = gpd.GeoDataFrame(
            geometry=[box(minx, miny, maxx, maxy)],
            crs="EPSG:4326",
        )
        world_size, _ = compute_world_params(initial_bounds, page_size=page_size, snap_to_pow2=True)
        square_bounds = make_square_bounds_centered(initial_bounds, world_size)
        data["bounds"] = square_bounds
    except Exception as exc:
        log_warning(logger, f"Could not square bounds: {exc}")
        data["bounds"] = bounds_gdf

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
        )
        console.print("[green]✓ Export complete:[/green]")
        for label, path in output_files.items():
            if path:
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