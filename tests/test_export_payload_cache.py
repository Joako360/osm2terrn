from __future__ import annotations

from pathlib import Path

from osm2terrn.cache.file_cache import FileCacheBackend
from osm2terrn.cache.manager import CacheManager
from osm2terrn.processing.otc import otc_global
from osm2terrn.processing.terrain import terrn2_entrypoint


def test_export_global_otc_reuses_cached_payload(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(otc_global, "get_cache_manager", lambda: manager)

    calls = {"count": 0}

    def fake_render(*args, **kwargs):
        calls["count"] += 1
        return "WorldSizeX=1\nWorldSizeZ=1\nWorldSizeY=1\nPageSize=1025\n"

    monkeypatch.setattr(otc_global, "_render_global_otc_content", fake_render)

    out_a = tmp_path / "a.otc"
    out_b = tmp_path / "b.otc"
    otc_global.export_global_otc(str(out_a), "page.otc", 1, 1, world_size_y=1, page_size=1025)
    otc_global.export_global_otc(str(out_b), "page.otc", 1, 1, world_size_y=1, page_size=1025)

    assert calls["count"] == 1
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")


def test_export_terrn2_reuses_cached_payload(monkeypatch, tmp_path: Path) -> None:
    manager = CacheManager(FileCacheBackend(tmp_path / "cache"), enabled=True)
    monkeypatch.setattr(terrn2_entrypoint, "get_cache_manager", lambda: manager)

    calls = {"count": 0}

    def fake_render(**kwargs):
        calls["count"] += 1
        return "[General]\nName = Demo\n\n"

    monkeypatch.setattr(terrn2_entrypoint, "_render_terrn2_content", fake_render)

    out_a = tmp_path / "a.terrn2"
    out_b = tmp_path / "b.terrn2"
    terrn2_entrypoint.export_terrn2_entrypoint(
        filepath=str(out_a),
        terrain_name="Demo",
        geometry_config="demo.otc",
        objects_files=["demo.tobj"],
        guid="00000000-0000-0000-0000-000000000001",
    )
    terrn2_entrypoint.export_terrn2_entrypoint(
        filepath=str(out_b),
        terrain_name="Demo",
        geometry_config="demo.otc",
        objects_files=["demo.tobj"],
        guid="00000000-0000-0000-0000-000000000001",
    )

    assert calls["count"] == 1
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")
