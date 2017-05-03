"""Configuration file parsing"""

from configparserplus import ConfigParserPlus

__all__ = ['config']

config = ConfigParserPlus('/etc/appcmd.conf')
