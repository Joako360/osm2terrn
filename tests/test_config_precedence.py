from __future__ import annotations

import pytest

from osm2terrn.config.loader import ProjectLoader


def test_project_loader_precedence_defaults_project_cli_interface(tmp_path):
    project_file = tmp_path / "project.toml"
    project_file.write_text(
        """
[terrain]
page_size = 2049

[export]
output_name = "project_name"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loader = ProjectLoader()
    cfg = loader.load_project_config(
        config_file=project_file,
        cli_overrides={
            "terrain": {"page_size": 4097},
            "export": {"output_name": "cli_name"},
        },
        interface_overrides={
            "terrain": {"page_size": 8193},
            "export": {"output_name": "ui_name"},
        },
    )

    assert cfg.terrain.page_size == 8193
    assert cfg.export.output_name == "ui_name"


def test_project_loader_includes_merge_project_fragments(tmp_path):
    project_file = tmp_path / "project.toml"
    roads_file = tmp_path / "roads.toml"
    terrain_file = tmp_path / "terrain.toml"

    project_file.write_text(
        """
include = ["roads.toml", "terrain.toml"]

[export]
output_name = "included_project"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    roads_file.write_text(
        """
[roads]
network_type = "bike"
default_width = 4.5
""".strip()
        + "\n",
        encoding="utf-8",
    )
    terrain_file.write_text(
        """
[terrain]
page_size = 2049
""".strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = ProjectLoader().load_project_config(config_file=project_file)

    assert cfg.export.output_name == "included_project"
    assert cfg.roads.network_type == "bike"
    assert cfg.roads.default_width == 4.5
    assert cfg.terrain.page_size == 2049


def test_project_loader_legacy_overrides_still_work(tmp_path):
    project_file = tmp_path / "project.toml"
    project_file.write_text(
        """
[terrain]
page_size = 2049
""".strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = ProjectLoader().load_project_config(
        config_file=project_file,
        overrides={"terrain": {"page_size": 4097}},
    )

    assert cfg.terrain.page_size == 4097


def test_project_loader_detects_circular_includes(tmp_path):
    a_file = tmp_path / "a.toml"
    b_file = tmp_path / "b.toml"

    a_file.write_text('include = ["b.toml"]\n', encoding="utf-8")
    b_file.write_text('include = ["a.toml"]\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Circular config include"):
        ProjectLoader().load_project_config(config_file=a_file)
