#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='appcmd',
    version='latest',
    author='Richard Neumann',
    requires=['homeinfo.crm', 'openimmo'],
    packages=['appcmd'],
    scripts=['files/appcmd-private', 'files/appcmd-public'],
    data_files=[
        ('/usr/lib/systemd/system', [
            'files/appcmd-private.service',
            'files/appcmd-public.service'])],
    description='Digital Sigange Flash Application communication interface')
