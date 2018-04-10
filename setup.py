#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='appcmd',
    version='latest',
    author='Richard Neumann',
    requires=['homeinfo.crm', 'openimmo'],
    packages=['appcmd'],
    description='Digital Sigange Flash Application communication interface')
