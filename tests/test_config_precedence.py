from __future__ import annotations

import pytest

from osm2terrn.config.validator import ConfigurationError
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


def test_program_config_loads_overpass_endpoints_and_limits(monkeypatch) -> None:
    monkeypatch.setenv("OVERPASS_URL", "https://primary.example/api")
    monkeypatch.setenv(
        "OVERPASS_ALTERNATE_URLS",
        "https://alternate-one.example/api, https://alternate-two.example/api",
    )
    monkeypatch.setenv("OVERPASS_MAX_ATTEMPTS", "4")
    monkeypatch.setenv("OVERPASS_MAX_ELAPSED_SECONDS", "90")

    config = ProjectLoader().load_program_config()

    assert config.osm.overpass_endpoints == (
        "https://primary.example/api",
        "https://alternate-one.example/api",
        "https://alternate-two.example/api",
    )
    assert config.osm.overpass_max_attempts == 4
    assert config.osm.overpass_max_elapsed_seconds == 90


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://user:password@overpass.example/api",
        "https://overpass.example/api?key=value",
        "file:///tmp/overpass",
    ],
)
def test_program_config_rejects_sensitive_or_invalid_overpass_urls(
    monkeypatch, endpoint: str
) -> None:
    monkeypatch.setenv("OVERPASS_URL", endpoint)
    monkeypatch.delenv("OVERPASS_ALTERNATE_URLS", raising=False)

    with pytest.raises(ConfigurationError, match="HTTP\\(S\\) URLs"):
        ProjectLoader().load_program_config()
