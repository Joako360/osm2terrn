import logging
from typing import Optional

def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured logger instance.

    Args:
        name (str): Name of the logger.
        log_file (Optional[str]): If provided, logs will also be written to this file.
        level (int): Logging level (default: logging.INFO).

    Returns:
        logging.Logger: Configured logger object.

    Example:
        logger = get_logger("osm2terrn")
        log_info(logger, "Logger initialized 🎉")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Remove existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
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