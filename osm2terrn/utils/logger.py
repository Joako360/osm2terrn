import logging
import os
from pathlib import Path
from typing import Optional


def _resolve_logging_level() -> int:
    raw_level = os.getenv("OSM2TERRN_LOG_LEVEL", "INFO").strip()
    if raw_level.isdigit():
        return int(raw_level)
    return int(getattr(logging, raw_level.upper(), logging.INFO))


def _resolve_default_log_file() -> Optional[Path]:
    raw_path = os.getenv("OSM2TERRN_LOG_FILE", "").strip()
    if not raw_path:
        return None
    return Path(raw_path)


def _resolve_logging_formatter() -> logging.Formatter:
    fmt = os.getenv("OSM2TERRN_LOG_FORMAT", "%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    datefmt = os.getenv("OSM2TERRN_LOG_DATEFMT", "%Y-%m-%d %H:%M:%S")
    return logging.Formatter(fmt, datefmt=datefmt)


def _ensure_logging_dirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, log_file: Optional[str] = None, level: Optional[int] = None) -> logging.Logger:
    """
    Returns a configured logger instance.

    Args:
        name (str): Name of the logger.
        log_file (Optional[str]): If provided, logs will also be written to this file.
        level (int): Logging level (default: from centralized config).

    Returns:
        logging.Logger: Configured logger object.

    Example:
        logger = get_logger("osm2terrn")
        log_info(logger, "Logger initialized 🎉")
    """
    effective_level = _resolve_logging_level() if level is None else level
    default_log_file = _resolve_default_log_file()
    effective_log_file = log_file or (str(default_log_file) if default_log_file is not None else None)

    logger = logging.getLogger(name)
    logger.setLevel(effective_level)
    formatter = _resolve_logging_formatter()

    # Remove existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(effective_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if effective_log_file:
        _ensure_logging_dirs(Path(effective_log_file))
        fh = logging.FileHandler(effective_log_file)
        fh.setLevel(effective_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def log_info(logger: logging.Logger, message: str) -> None:
    """Logs an info message."""
    logger.info(message)

def log_warning(logger: logging.Logger, message: str) -> None:
    """Logs a warning message."""
    logger.warning(message)

def log_error(logger: logging.Logger, message: str) -> None:
    """Logs an error message."""
    logger.error(message)

def log_debug(logger: logging.Logger, message: str) -> None:
    """Logs a debug message."""
    logger.debug(message)

def log_exception(logger: logging.Logger, message: str) -> None:
    """Logs an error message with exception traceback."""
    logger.exception(message)