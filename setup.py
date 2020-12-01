#! /usr/bin/env python3
"""Install script."""

from distutils.core import setup


setup(
    name='appcmd',
    version='latest',
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo priod de>',
    requires=['mdb', 'openimmo', 'damage_report', 'tenant2tenant'],
    packages=['appcmd', 'appcmd.dom', 'appcmd.update'],
    description='Digital Signange Flash Application communication interface.'
)
