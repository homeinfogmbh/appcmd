"""Garbage collection info retrieval."""

from requests import ConnectionError as ConnectionError_

from aha import LocationNotFound, AhaDisposalClient
from wsgilib import JSON

from appcmd.functions import street_houseno

__all__ = ['garbage_collection']


AHA_CLIENT = AhaDisposalClient()


def garbage_collection():
    """Returns information about the garbage collection."""

    try:
        pickups = tuple(AHA_CLIENT.by_street_houseno(*street_houseno()))
    except ConnectionError_:
        return ('Could not connect to AHA API.', 503)
    except LocationNotFound:
        return ('Location not found.', 404)

    return JSON([pickup.to_dict() for pickup in pickups])
