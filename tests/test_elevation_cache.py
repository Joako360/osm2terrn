from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pytest
import rasterio
import requests

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.processing.terrain import elevation_service
from osm2terrn.processing.terrain.heightmap_handler import _prepare_elevation_data


def test_load_elevation_raster_uses_cache(monkeypatch, tmp_path: Path) -> None:
    call_counter = {"count": 0}

    def fake_download(_params):
        call_counter["count"] += 1
        dem = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=float)
        return dem, rasterio.Affine.identity(), float(np.nanmax(dem)), float(np.nanmin(dem))

    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(elevation_service, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(elevation_service, "_download_elevation_raster", fake_download)

    bounds = (-58.52, -34.76, -58.50, -34.74)
    first = elevation_service.load_elevation_raster(bounds)
    second = elevation_service.load_elevation_raster(bounds)

    assert call_counter["count"] == 1
    assert np.array_equal(first[0], second[0])
    assert first[2] == second[2]
    assert first[3] == second[3]


def test_elevation_sampler_zero_fills_points_outside_raster() -> None:
    from rasterio.transform import from_bounds

    elevation = np.full((28, 43), 92.0, dtype=float)
    transform = from_bounds(
        -122.41306,
        37.80111,
        -122.40111,
        37.80889,
        width=43,
        height=28,
    )

    sampled = elevation_service.sample_elevation_at_coords(
        lon=np.array([-122.407, -122.407]),
        lat=np.array([37.804, 37.80101]),
        elevation=elevation,
        transform=transform,
    )

    assert sampled[0] == pytest.approx(92.0)
    assert sampled[1] == 0.0


def test_http_error_does_not_log_or_propagate_api_key(monkeypatch, tmp_path: Path, caplog, capsys) -> None:
    api_key = "opentopo-test-secret-9f2d"

    class FailedResponse:
        status_code = 502

        @property
        def content(self) -> bytes:
            return b""

        def raise_for_status(self) -> None:
            raise requests.HTTPError(
                f"502 Server Error for url: https://example.test/globaldem?API_Key={api_key}",
                response=self,
            )

    def fake_get(_url, *, params, stream):
        assert params["API_Key"] == api_key
        assert stream is True
        return FailedResponse()

    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(elevation_service, "get_cache_manager", lambda: manager)
    monkeypatch.setattr(elevation_service.requests, "get", fake_get)
    monkeypatch.setenv(elevation_service._PROGRAM_CONFIG.providers.opentopo_api_key_env_var, api_key)

    caplog.set_level(logging.ERROR)
    with pytest.raises(RuntimeError, match="HTTP 502") as error:
        elevation_service._download_elevation_raster({"API_Key": api_key})
    assert error.value.__context__ is None
    for sensitive_value in (api_key, api_key[:3], api_key[-3:]):
        assert sensitive_value not in str(error.value)

    result = _prepare_elevation_data(
        bounds=(-58.52, -34.76, -58.50, -34.74),
        elevation_data=None,
        output_size=(2, 2),
    )
    terminal_output = capsys.readouterr()
    captured = caplog.text + terminal_output.out + terminal_output.err

    assert result[1:] == (0.0, 0.0, "failed")
    assert "HTTP 502" in captured
    assert api_key not in captured
    assert api_key[:3] not in captured
    assert api_key[-3:] not in captured
    assert "example.test" not in captured
