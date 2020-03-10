"""Statistics submission."""

from flask import request

from digsigdb import Statistics

from appcmd.functions import get_deployment


__all__ = ['add_statistics']


def add_statistics():
    """Adds a new statistics entry."""

    Statistics.add(get_deployment(), request.args['document'])
    return ('Statistics added.', 201)
