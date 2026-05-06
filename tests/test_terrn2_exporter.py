from pathlib import Path

from src.processing.terrn2_exporter import export_terrn2_entrypoint


def test_export_terrn2_entrypoint_writes_expected_sections(tmp_path: Path):
    out = tmp_path / "demo.terrn2"
    export_terrn2_entrypoint(
        filepath=str(out),
        terrain_name="Demo Terrain",
        geometry_config="demo.otc",
        objects_files=["demo.tobj", "roads.tobj"],
        authors=["osm2terrn", "OpenStreetMap Contributors"],
        guid="12345678-1234-1234-1234-123456789abc",
        scripts=["init.as"],
        ai_presets=["ai.json"],
    )

    text = out.read_text(encoding="utf-8")
    assert "[General]" in text
    assert "Name = Demo Terrain" in text
    assert "GeometryConfig = demo.otc" in text
    assert "GUID = 12345678-1234-1234-1234-123456789abc" in text

    assert "[Authors]" in text
    assert "osm2terrn" in text

    assert "[Objects]" in text
    assert "demo.tobj=" in text
    assert "roads.tobj=" in text

    assert "[Scripts]" in text
    assert "init.as=" in text
    assert "[AI Presets]" in text
    assert "ai.json=" in text
