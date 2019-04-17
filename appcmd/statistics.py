"""Statistics submission."""

from flask import request

from digsigdb import Statistics

from appcmd.functions import get_system


__all__ = ['add_statistics']


def add_statistics():
    """Adds a new statistics entry."""

    system = get_system()
    deployment = system.deployment

    if deployment is None:
        return ('System is not deployed.', 400)

    Statistics.add(deployment, request.args['document'])
    return ('Statistics added.', 201)
