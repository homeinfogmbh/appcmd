"""Statistics submission."""

from flask import request

from digsigdb import Statistics

from appcmd.functions import get_system


__all__ = ['add_statistics']


def add_statistics():
    """Adds a new statistics entry."""

    system = get_system()
    location = system.location

    if location is None:
        return ('System is not located.', 400)

    Statistics.add(location.address, request.args['document'])
    return ('Statistics added.', 201)
