"""Simple structured logging shared by both services."""
import logging
import sys

_CONFIGURED = False


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a configured logger. Safe to call many times."""
    global _CONFIGURED
    if not _CONFIGURED:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(level.upper())
        _CONFIGURED = True

    return logging.getLogger(name)
