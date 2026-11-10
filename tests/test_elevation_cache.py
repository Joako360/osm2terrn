from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.processing.terrain import elevation_service


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
