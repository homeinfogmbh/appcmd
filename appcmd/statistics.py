"""Statistics submission."""

from digsigdb import Statistics

from flask import request

from appcmd.functions import get_customer


__all__ = ['add_statistics']


def add_statistics():
    """Adds a new statistics entry."""

    Statistics.add(
        get_customer(), request.args['vid'], request.args.get('tid'),
        request.args['document'])
    return ('Statistics added.', 201)
