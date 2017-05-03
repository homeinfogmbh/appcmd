#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='appcmd',
    version='latest',
    author='Richard Neumann',
    requires=[
        'docopt',
        'setproctitle',
        'homeinfo.lib',
        'homeinfo.crm',
        'openimmo'],
    packages=['appcmd'],
    data_files=[('/usr/local/share/appcmd', ['files/appcmd.wsgi'])],
    description='Digital Sigange Flash Application communication interface')
