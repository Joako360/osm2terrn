from osm2terrn.processing.orchestrator import _normalize_place_for_filename


def test_normalize_place_for_filename_uses_city_name_only():
    place = "Buenos Aires, Buenos Aires, Argentina"
    assert _normalize_place_for_filename(place) == "Buenos Aires"


def test_normalize_place_for_filename_handles_single_city_name():
    place = "Cordoba"
    assert _normalize_place_for_filename(place) == "Cordoba"


def test_normalize_place_for_filename_strips_invalid_filename_chars():
    place = "Test/City:Name?*|<>, Buenos Aires, Argentina"
    assert _normalize_place_for_filename(place) == "TestCityName"


def test_normalize_place_for_filename_returns_terrain_for_empty_place():
    assert _normalize_place_for_filename("") == "terrain"
