"""
src/utils/logger.py
Centralised rotating-file + console logger.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import settings

_loggers: dict = {}


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (cached). Creates handlers on first call."""
    if name in _loggers:
        return _loggers[name]

    os.makedirs(settings.LOG_DIR, exist_ok=True)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)

    # Rotating file handler (10 MB × 5 backups)
    fh = RotatingFileHandler(
        os.path.join(settings.LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.propagate = False

    _loggers[name] = logger
    return logger
