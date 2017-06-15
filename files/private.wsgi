#! /usr/bin/env python3

from wsgilib import RestApp
from appcmd.wsgi import PrivateHandler

application = RestApp(PrivateHandler)
