from __future__ import annotations

import pytest

from osm2terrn.app.main import _build_parser, _build_program_cli_overrides, _build_project_cli_overrides


def test_cli_builds_project_overrides_from_real_args():
    parser = _build_parser()
    args = parser.parse_args(
        [
            "--terrain-page-size",
            "4097",
            "--terrain-output-width",
            "2049",
            "--terrain-output-height",
            "2049",
            "--roads-network-type",
            "all",
            "--roads-no-simplify",
            "--export-output-name",
            "my_city",
            "--pipeline-no-preload-elevation",
        ]
    )

    overrides = _build_project_cli_overrides(args)

    assert overrides["terrain"]["page_size"] == 4097
    assert overrides["terrain"]["output_size"] == [2049, 2049]
    assert overrides["roads"]["network_type"] == "all"
    assert overrides["roads"]["simplify"] is False
    assert overrides["export"]["output_name"] == "my_city"
    assert overrides["pipeline"]["preload_elevation"] is False


def test_cli_builds_program_overrides_from_real_args():
    parser = _build_parser()
    args = parser.parse_args(
        [
            "--output-dir",
            "./output_test",
            "--logs-dir",
            "./logs_test",
            "--cache-dir",
            "./cache_test",
        ]
    )

    overrides = _build_program_cli_overrides(args)

    assert overrides["paths"]["output_dir"] == "./output_test"
    assert overrides["paths"]["logs_dir"] == "./logs_test"
    assert overrides["paths"]["cache_dir"] == "./cache_test"


def test_cli_rejects_half_output_size_pair():
    parser = _build_parser()
    args = parser.parse_args(["--terrain-output-width", "1025"])

    with pytest.raises(ValueError, match="required together"):
        _build_project_cli_overrides(args)
