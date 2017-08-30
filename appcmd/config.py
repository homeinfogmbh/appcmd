"""Configuration file parsing"""

from configparserplus import ConfigParserPlus

__all__ = ['CONFIG']

CONFIG = ConfigParserPlus('/etc/appcmd.conf')
