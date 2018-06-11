#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='appcmd',
    version='latest',
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo priod de>',
    requires=['homeinfo.crm', 'openimmo'],
    packages=['appcmd'],
    description='Digital Sigange Flash Application communication interface')
