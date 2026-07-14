"""Central accessors for active program/project configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from osm2terrn.config.loader import ProjectLoader
from osm2terrn.config.models import ProgramConfig, ProjectConfig

_LOADER = ProjectLoader()
_PROGRAM_CONFIG: ProgramConfig | None = None
_PROJECT_CONFIG: ProjectConfig | None = None


def configure(
    *,
    program_config: ProgramConfig | None = None,
    project_config: ProjectConfig | None = None,
) -> None:
    """Inject active configuration objects explicitly."""

    global _PROGRAM_CONFIG, _PROJECT_CONFIG
    _PROGRAM_CONFIG = program_config
    _PROJECT_CONFIG = project_config


def reset() -> None:
    """Reset active configuration cache."""

    configure(program_config=None, project_config=None)


def get_program_config(
    *,
    cli_overrides: Mapping[str, Any] | None = None,
    interface_overrides: Mapping[str, Any] | None = None,
) -> ProgramConfig:
    """Return active internal program config, lazily loading defaults and precedence layers."""

    global _PROGRAM_CONFIG
    if _PROGRAM_CONFIG is None:
        _PROGRAM_CONFIG = _LOADER.load_program_config(
            cli_overrides=cli_overrides,
            interface_overrides=interface_overrides,
        )
    return _PROGRAM_CONFIG


def get_project_config(
    project_root: str | Path | None = None,
    *,
    cli_overrides: Mapping[str, Any] | None = None,
    interface_overrides: Mapping[str, Any] | None = None,
) -> ProjectConfig:
    """Return active project config using precedence: defaults -> project -> CLI -> interface."""

    global _PROJECT_CONFIG
    if _PROJECT_CONFIG is None:
        _PROJECT_CONFIG = _LOADER.load_project_config(
            project_root=project_root,
            cli_overrides=cli_overrides,
            interface_overrides=interface_overrides,
        )
    return _PROJECT_CONFIG


def load_project(
    project_root: str | Path | None = None,
    *,
    cli_overrides: Mapping[str, Any] | None = None,
    interface_overrides: Mapping[str, Any] | None = None,
) -> ProjectConfig:
    """Load and set active project configuration from a project directory with precedence layers."""

    global _PROJECT_CONFIG
    _PROJECT_CONFIG = _LOADER.load_project_config(
        project_root=project_root,
        cli_overrides=cli_overrides,
        interface_overrides=interface_overrides,
    )
    return _PROJECT_CONFIG


def get_project_loader() -> ProjectLoader:
    """Expose loader instance as single entrypoint facade."""

    return _LOADER
