from __future__ import annotations

from pathlib import Path

import numpy as np

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.processing.terrain import heightmap_handler


def test_generate_heightmap_uses_smoothed_cache(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(heightmap_handler, "get_cache_manager", lambda: manager)

    gaussian_calls = {"count": 0}

    def fake_prepare(bounds, elevation_data, output_size):
        elevation = np.array([[0.0, 1.0], [0.5, 0.2]], dtype=float)
        return elevation, 10.0, 0.0

    def fake_gaussian(arr, sigma):
        gaussian_calls["count"] += 1
        return arr

    saved = {"count": 0}

    def fake_save(**kwargs):
        saved["count"] += 1

    monkeypatch.setattr(heightmap_handler, "_prepare_elevation_data", fake_prepare)
    monkeypatch.setattr(heightmap_handler.scipy.ndimage, "gaussian_filter", fake_gaussian)
    monkeypatch.setattr(heightmap_handler, "_save_map_image", fake_save)

    bounds = (-58.52, -34.76, -58.50, -34.74)
    stats_a = heightmap_handler.generate_heightmap_n_texture(bounds, "a.png", "b.png")
    stats_b = heightmap_handler.generate_heightmap_n_texture(bounds, "a.png", "b.png")

    assert gaussian_calls["count"] == 1
    assert saved["count"] == 4
    assert stats_a == stats_b
