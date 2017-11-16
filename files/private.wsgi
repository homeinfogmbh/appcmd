#! /usr/bin/env python3

from wsgilib import RestApp
from appcmd.wsgi import PRIVATE

application = RestApp(PRIVATE)
