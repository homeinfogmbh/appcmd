"""Configuration file parsing."""

from configlib import INIParser

__all__ = ['CONFIG', 'MAX_MSG_SIZE']

CONFIG = INIParser('/etc/appcmd.conf')

try:
    MAX_MSG_SIZE = int(CONFIG['max_msg_size'])
except KeyError:
    MAX_MSG_SIZE = 2048
