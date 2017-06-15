#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='appcmd',
    version='latest',
    author='Richard Neumann',
    requires=[
        'wsgilib',
        'setproctitle',
        'homeinfo.lib',
        'homeinfo.crm',
        'openimmo'],
    packages=['appcmd'],
    data_files=[
        ('/usr/local/share/appcmd', [
            'files/private.wsgi',
            'files/public.wsgi']),
        ('/etc/uwsgi/apps-available', [
            'files/appcmd-private.ini',
            'files/appcmd-public.ini'])],
    description='Digital Sigange Flash Application communication interface')
