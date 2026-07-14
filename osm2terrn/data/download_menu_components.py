from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from rich.table import Table
from osm2terrn.cli.components import MenuRenderer


class DownloadAction(Enum):
    SEARCH_PLACE = "search_place"
    CUSTOM_BBOX = "custom_bbox"
    CANCEL = "cancel"


@dataclass
class NominatimResult:
    display_name: str
    result_type: str
    result_class: str
    osm_type: str
    boundingbox: List[str]

    @property
    def is_enclosed_area(self) -> bool:
        return self.result_type == 'administrative' or self.result_class == 'boundary'

    def get_bbox_tuple(self) -> Tuple[float, float, float, float]:
        return (
            float(self.boundingbox[2]),
            float(self.boundingbox[0]),
            float(self.boundingbox[3]),
            float(self.boundingbox[1]),
        )

    def get_city_name(self) -> str:
        """Return the first component of the display name as the city name."""
        return self.display_name.split(",")[0].strip()


class DownloadMenuRenderer(MenuRenderer):
    def render_bbox_input_help(self) -> None:
        self.render_panel(
            "[yellow]Remember:[/yellow]\n"
            "• West (xmin) < East (xmax)\n"
            "• South (ymin) < North (ymax)\n"
            "• Longitudes: -180 to 180\n"
            "• Latitudes: -90 to 90",
            title="Enter custom bounding box limits",
            border_style="blue",
        )

    def render_search_results(self, place: str, results: List[NominatimResult]) -> None:
        self.console.print()
        table = Table(
            title=f"[bold green]Search Results for '{place}'[/bold green]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Option", style="cyan", justify="center", width=6)
        table.add_column("Display Name", style="white", width=50, overflow="ellipsis")
        table.add_column("Type", style="yellow", width=14)
        table.add_column("Class", style="blue", width=10)

        for idx, result in enumerate(results, start=1):
            display_name = result.display_name[:50]
            result_type = result.result_type[:14]
            result_class = result.result_class[:10]
            if result.is_enclosed_area:
                row_style = "green"
            elif result.osm_type != 'relation':
                row_style = "red"
            else:
                row_style = "white"
            table.add_row(str(idx), display_name, result_type, result_class, style=row_style)

        self.console.print(table)
        self.console.print("[dim green]💡 Green rows: Enclosed areas (administrative/boundary)[/dim green]")
        self.console.print("[dim red]💡 Red rows: Non-enclosed areas[/dim red]")
