#! /usr/bin/env python3
"""Install script."""

from setuptools import setup


setup(
    name='appcmd',
    use_scm_version={
        "local_scheme": "node-and-timestamp"
    },
    setup_requires=['setuptools_scm'],
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo priod de>',
    install_requires=[
        'aha',
        'bookings',
        'cleaninglog',
        'cmslib',
        'configlib',
        'damage_report',
        'digsigdb',
        'emaillib',
        'flask',
        'hwdb',
        'lptlib',
        'mdb',
        'peeweeplus',
        'requests',
        'setuptools',
        'tenant2landlord',
        'tenant2tenant',
        'timelib',
        'wsgilib',
    ],
    packages=['appcmd', 'appcmd.update'],
    description='Digital Signange Flash Application communication interface.'
)
