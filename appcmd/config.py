"""Configuration file parsing."""

from configparser import ConfigParser


__all__ = ['CONFIG']


CONFIG = ConfigParser()
CONFIG.read('/usr/local/etc/appcmd.conf')
