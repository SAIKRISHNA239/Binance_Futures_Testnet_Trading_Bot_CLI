"""
Logging configuration for the trading bot.

Configures file logging to logs/trading.log and optional console output.
"""

import logging
import os
from pathlib import Path


def setup_logging(
    log_dir: str = "logs",
    log_file: str = "trading.log",
    level: int = logging.INFO,
    console: bool = False,
) -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        log_dir: Directory for log files.
        log_file: Log file name.
        level: Logging level (default INFO).
        console: If True, also log to console.

    Returns:
        Configured logger instance.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file_path = log_path / log_file

    logger = logging.getLogger("trading_bot")
    logger.setLevel(level)

    # Avoid adding handlers multiple times (e.g. in tests or reloads)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get the trading_bot logger or a child logger."""
    if name:
        return logging.getLogger(f"trading_bot.{name}")
    return logging.getLogger("trading_bot")
