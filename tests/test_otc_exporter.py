from pathlib import Path

from osm2terrn.processing.otc.otc_global import export_global_otc
from osm2terrn.processing.otc.otc_paged import export_paged_otc


def test_export_global_otc_writes_core_fields(tmp_path: Path):
    out = tmp_path / "terrain.otc"
    export_global_otc(
        filepath=str(out),
        page_file_format="my-page-0-0.otc",
        world_size_x=2048,
        world_size_z=2048,
        world_size_y=250,
        page_size=1025,
    )

    text = out.read_text(encoding="utf-8")
    assert "WorldSizeX=2048" in text
    assert "WorldSizeZ=2048" in text
    assert "WorldSizeY=250" in text
    assert "PageSize=1025" in text
    assert "PageFileFormat=my-page-0-0.otc" in text
    assert "disableCaching=1" in text


def test_export_paged_otc_builds_default_layers_when_groundmap_given(tmp_path: Path):
    out = tmp_path / "my-page-0-0.otc"
    export_paged_otc(
        filepath=str(out),
        heightmap_png="height.png",
        groundmap_file="ground.png",
        layers=None,
    )

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "height.png"
    # Current behavior: 1 base layer + 1 blended layer using the groundmap
    assert lines[1] == "2"
    assert any("ground.png, G" in line for line in lines)
