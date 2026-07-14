"""Path resolution helpers for configuration loading."""

from __future__ import annotations

from pathlib import Path


def get_workspace_root() -> Path:
    """Return repository root inferred from package location."""

    return Path(__file__).resolve().parents[2]


def default_output_dir(workspace_root: Path | None = None) -> Path:
    """Return default output directory path."""

    root = workspace_root or get_workspace_root()
    return root / "output"


def default_logs_dir(workspace_root: Path | None = None) -> Path:
    """Return default logs directory path."""

    root = workspace_root or get_workspace_root()
    return root / "logs"


def default_cache_dir(workspace_root: Path | None = None) -> Path:
    """Return default cache directory path."""

    root = workspace_root or get_workspace_root()
    return root / ".cache"


def default_projects_dir(workspace_root: Path | None = None) -> Path:
    """Return default projects directory path."""

    root = workspace_root or get_workspace_root()
    return root / "projects"
