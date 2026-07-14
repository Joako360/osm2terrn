from collections import OrderedDict
from typing import Optional, Tuple

import osmnx as ox

from osm2terrn.cli.components import MenuOption
from osm2terrn.data.download_menu_components import (
    DownloadAction,
    DownloadMenuRenderer,
    NominatimResult,
)


class DownloadMenu:
    def __init__(self, renderer: Optional[DownloadMenuRenderer] = None):
        self.renderer = renderer or DownloadMenuRenderer()
        self.options = [
            MenuOption(action_id=DownloadAction.SEARCH_PLACE, display_key="1", label="Search by place name", icon="🔍"),
            MenuOption(action_id=DownloadAction.CUSTOM_BBOX, display_key="2", label="Enter custom bounding box", icon="📐"),
            MenuOption(action_id=DownloadAction.CANCEL, display_key="0", label="Cancel", icon="❌"),
        ]

    def get_option_by_key(self, key: str) -> Optional[MenuOption]:
        return next((opt for opt in self.options if opt.display_key == key), None)

    def show_main_menu(self) -> Tuple[str, Optional[Tuple[float, float, float, float]]]:
        while True:
            self.renderer.render_menu("Select download mode", self.options, border_style="magenta")
            choice = self.renderer.get_user_input("Enter option (0/1/2):")
            option = self.get_option_by_key(choice)
            if option:
                if option.action_id == DownloadAction.SEARCH_PLACE:
                    place = self.search_place()
                    if not place:
                        continue

                    results = self.search_nominatim(place)
                    if not results:
                        self.renderer.render_error("No search results found. Try a different place name.")
                        continue

                    selected_result = self.show_search_results(place, results)
                    if selected_result is None:
                        continue

                    return selected_result.get_city_name(), selected_result.get_bbox_tuple()

                if option.action_id == DownloadAction.CUSTOM_BBOX:
                    return "", self.get_custom_bbox()

                if option.action_id == DownloadAction.CANCEL:
                    return "", None

            self.renderer.render_error("Invalid option. Please enter 0, 1, or 2.")

    def get_custom_bbox(self) -> Tuple[float, float, float, float]:
        self.renderer.render_bbox_input_help()

        def get_float(prompt: str, minval: float, maxval: float) -> float:
            while True:
                try:
                    val = float(self.renderer.get_user_input(prompt))
                    if val < minval or val > maxval:
                        self.renderer.render_error(f"Value must be between {minval} and {maxval}.")
                        continue
                    return val
                except ValueError:
                    self.renderer.render_error("Invalid number. Please try again.")

        west = get_float("West (xmin, min longitude): ", -180.0, 180.0)
        south = get_float("South (ymin, min latitude): ", -90.0, 90.0)
        east = get_float("East (xmax, max longitude): ", -180.0, 180.0)
        north = get_float("North (ymax, max latitude): ", -90.0, 90.0)

        if west >= east or south >= north:
            self.renderer.render_error("Invalid bounding box: west must be < east and south < north.")
            return self.get_custom_bbox()
        return (west, south, east, north)

    def search_place(self) -> str:
        while True:
            place = self.renderer.get_user_input("Enter the place name (or 0 to cancel):")
            if place == '0':
                return ""
            if place:
                return place
            self.renderer.render_error("Please enter a valid place name or 0 to cancel.")

    def search_nominatim(self, place: str) -> list[NominatimResult]:
        nmntm_req = OrderedDict([('q', place), ('format', 'json')])
        results = ox._nominatim._nominatim_request(nmntm_req)  # type: ignore
        return [
            NominatimResult(
                display_name=result['display_name'],
                result_type=result['type'],
                result_class=result['class'],
                osm_type=result['osm_type'],
                boundingbox=result['boundingbox'],
            )
            for result in results
        ]

    def show_search_results(self, place: str, results: list[NominatimResult]) -> Optional[NominatimResult]:
        self.renderer.render_search_results(place, results)
        while True:
            sel = self.renderer.get_user_input(f"Which result? (1-{len(results)} or 0 to cancel): ")
            if sel == "0":
                return None
            try:
                si = int(sel)
            except ValueError:
                self.renderer.render_error("Invalid selection. Enter a number.")
                continue
            if not (1 <= si <= len(results)):
                self.renderer.render_error("Selection out of range. Try again.")
                continue
            return results[si - 1]
