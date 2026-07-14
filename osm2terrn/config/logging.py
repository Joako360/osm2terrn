"""Logging configuration helpers backed by ProgramConfig."""

from __future__ import annotations

import logging
from pathlib import Path

from osm2terrn.config.settings import get_program_config


def ensure_logging_dirs() -> None:
    """Ensure log directory exists according to configuration."""

    cfg = get_program_config()
    cfg.paths.logs_dir.mkdir(parents=True, exist_ok=True)


def resolve_default_log_file() -> Path | None:
    """Resolve default log file path from active config."""

    cfg = get_program_config()
    return cfg.logging.default_log_file


def resolve_logging_level() -> int:
    """Resolve default logging level from active config."""

    cfg = get_program_config()
    return int(cfg.logging.level)


def resolve_logging_formatter() -> logging.Formatter:
    """Resolve logging formatter from active config."""

    cfg = get_program_config()
    return logging.Formatter(cfg.logging.fmt, datefmt=cfg.logging.datefmt)
