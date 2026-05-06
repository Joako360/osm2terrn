import math

import geopandas as gpd
import pytest
from shapely.geometry import LineString
from shapely.geometry import box as shp_box

from src.utils.geometry_utils import (
    _next_power_of_two,
    bbox_size_meters,
    compute_world_params,
    utm_crs_from_lonlat,
)


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
    gdf = gpd.GeoDataFrame(geometry=[shp_box(0, 0, 1500, 1000)], crs="EPSG:3857")
    world_size, mpp = compute_world_params(gdf, page_size=1025, snap_to_pow2=True)
    assert world_size == 2048
    assert mpp == 2.0


def test_compute_world_params_without_pow2_snap():
    gdf = gpd.GeoDataFrame(geometry=[shp_box(0, 0, 1500, 1000)], crs="EPSG:3857")
    w_m, h_m = bbox_size_meters(gdf)
    world_size, mpp = compute_world_params(gdf, page_size=1025, snap_to_pow2=False)
    expected = math.ceil(max(w_m, h_m))
    assert world_size == expected
    assert mpp == expected / 1024


def test_compute_world_params_rejects_empty_bounds():
    empty = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    with pytest.raises(ValueError, match="empty"):
        compute_world_params(empty)
