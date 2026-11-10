import math

import geopandas as gpd
import pytest
from pyproj import Transformer
from shapely.geometry import box

from osm2terrn.utils.geometry.bounds import (
    _next_power_of_two,
    bbox_size_meters,
    compute_world_params,
)
from osm2terrn.utils.geometry import bounds as geometry_bounds
from osm2terrn.utils.geometry.crs import (
    utm_crs_from_lonlat,
)
from osm2terrn.domain.value_objects import BoundingBox

make_square_bounds_centered = getattr(geometry_bounds, "make_square_bounds_centered")


def test_utm_crs_from_lonlat_returns_expected_epsg():
    crs_north = utm_crs_from_lonlat(0.0, 10.0)
    crs_south = utm_crs_from_lonlat(0.0, -10.0)
    assert crs_north.to_epsg() == 32631
    assert crs_south.to_epsg() == 32731


def test_next_power_of_two_clamps_and_rounds_up():
    assert _next_power_of_two(100) == 1024
    assert _next_power_of_two(1500) == 2048
    assert _next_power_of_two(1 << 20) == 1 << 15


def test_compute_world_params_with_projected_bbox():
    # Projected bbox in meters (EPSG:3857): 1500m x 1000m
    gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 1500, 1000)], crs="EPSG:3857")
    world_size, mpp = compute_world_params(gdf, 1025, True)
    assert world_size == 2048
    assert mpp == 2.0


def test_compute_world_params_without_pow2_snap():
    gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 1500, 1000)], crs="EPSG:3857")
    w_m, h_m = bbox_size_meters(gdf)
    world_size, mpp = compute_world_params(gdf, 1025, False)
    expected = math.ceil(max(w_m, h_m))
    assert world_size == expected
    assert mpp == expected / 1024


def test_compute_world_params_uses_extent_of_all_geometries():
    gdf = gpd.GeoDataFrame(
        geometry=[box(0, 0, 100, 100), box(1200, 0, 1400, 100)],
        crs="EPSG:3857",
    )

    world_size, meters_per_pixel = compute_world_params(gdf, 1025, False)

    assert world_size == 1400
    assert meters_per_pixel == 1400 / 1024


def test_compute_world_params_rejects_unsupported_bounds():
    with pytest.raises(ValueError, match="Bounds are required"):
        compute_world_params(None)


def test_compute_world_params_reprojects_non_wgs84_geographic_bounds():
    bounds = BoundingBox(2.2, 48.8, 2.4, 49.0, crs="EPSG:4807", is_projected=False)
    to_wgs84 = Transformer.from_crs("EPSG:4807", "EPSG:4326", always_xy=True)
    corners = [
        to_wgs84.transform(x, y)
        for x, y in ((2.2, 48.8), (2.2, 49.0), (2.4, 48.8), (2.4, 49.0))
    ]
    expected_bounds = BoundingBox(
        min(point[0] for point in corners),
        min(point[1] for point in corners),
        max(point[0] for point in corners),
        max(point[1] for point in corners),
        crs="EPSG:4326",
        is_projected=False,
    )

    assert compute_world_params(bounds) == compute_world_params(expected_bounds)


def test_compute_world_params_rejects_empty_bounds():
    empty = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    with pytest.raises(ValueError, match="empty"):
        compute_world_params(empty)


def test_make_square_bounds_centered_returns_domain_bounding_box() -> None:
    bounds = BoundingBox(-58.52, -34.76, -58.50, -34.74, crs="EPSG:4326", is_projected=False)
    square = make_square_bounds_centered(bounds, 2048.0)

    assert isinstance(square, BoundingBox)
    assert square.width > 0.0
    assert square.height > 0.0


def test_validation_bounds_measurement_exposes_second_world_size_round_up() -> None:
    """Characterize the measured bounds expansion without choosing an output scale."""
    bounds = BoundingBox(
        -122.4130,
        37.8010,
        -122.4010,
        37.8100,
        crs="EPSG:4326",
        is_projected=False,
    )

    initial_width, initial_height = bbox_size_meters(bounds)
    first_world_size, _ = compute_world_params(bounds)
    square_bounds = make_square_bounds_centered(bounds, first_world_size)
    square_width, square_height = bbox_size_meters(square_bounds)
    second_world_size, _ = compute_world_params(square_bounds)

    assert initial_width == pytest.approx(1062.69, abs=0.1)
    assert initial_height == pytest.approx(1005.25, abs=0.1)
    assert first_world_size == 2048
    assert square_width == pytest.approx(2073.82, abs=0.1)
    assert square_height == pytest.approx(2048.0, abs=0.1)
    assert second_world_size == 4096
