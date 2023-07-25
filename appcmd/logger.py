"""Appcmd's logger."""

from logging import INFO, basicConfig, getLogger


__all__ = ["LOGGER", "init_logger"]


LOG_FORMAT = "[%(levelname)s] %(name)s: %(message)s"
LOGGER = getLogger("appcmd")


def init_logger():
    """Initializes the logger."""

    basicConfig(level=INFO, format=LOG_FORMAT)
