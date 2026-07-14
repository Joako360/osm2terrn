import pytest

from osm2terrn.data.download_menu import DownloadMenu, NominatimResult
from osm2terrn.data.osm_data_handler import download_menu


class DummyRenderer:
    def __init__(self, inputs):
        self.inputs = iter(inputs)
        self.prompts = []

    def render_menu(self, title: str, options: list, border_style: str = "magenta"):
        pass

    def render_bbox_input_help(self) -> None:
        pass

    def render_search_results(self, place: str, results: list[NominatimResult]) -> None:
        pass

    def render_error(self, message: str) -> None:
        pass

    def get_user_input(self, prompt: str) -> str:
        self.prompts.append(prompt)
        try:
            return next(self.inputs)
        except StopIteration:
            raise AssertionError("No more simulated inputs available")


def test_download_menu_search_place_returns_place_and_bbox():
    fake_results = [
        NominatimResult(
            display_name="Test City, Country",
            result_type="city",
            result_class="place",
            osm_type="relation",
            boundingbox=["-1.0", "-2.0", "1.0", "2.0"],
        )
    ]

    renderer = DummyRenderer(["1", "Test City", "1"])
    menu = DownloadMenu(renderer=renderer)
    menu.search_nominatim = lambda place: fake_results

    place, bbox = menu.show_main_menu()

    assert place == "Test City"
    assert bbox == (1.0, -1.0, 2.0, -2.0)


def test_download_menu_custom_bbox_returns_empty_place_and_bbox():
    renderer = DummyRenderer(["2", "-10.0", "-20.0", "10.0", "20.0"])
    menu = DownloadMenu(renderer=renderer)

    place, bbox = menu.show_main_menu()

    assert place == ""
    assert bbox == (-10.0, -20.0, 10.0, 20.0)


def test_download_menu_cancel_returns_empty_result():
    renderer = DummyRenderer(["0"])
    menu = DownloadMenu(renderer=renderer)

    place, bbox = menu.show_main_menu()

    assert place == ""
    assert bbox is None
