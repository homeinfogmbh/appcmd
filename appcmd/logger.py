"""Appcmd's logger."""

from logging import INFO, basicConfig, getLogger


__all__ = ['LOGGER']


LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
basicConfig(level=INFO, format=LOG_FORMAT)
LOGGER = getLogger('appcmd')
