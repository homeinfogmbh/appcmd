"""Return information about the system and deployment."""

from wsgilib import Error, JSON

from appcmd.functions import get_system


__all__ = ['get_deployment']


def get_deployment():
    """Returns information about the system's deployment."""

    deployment = get_system().deployment

    if deployment is None:
        return Error('System is not deployed.')

    return JSON(deployment.to_json(cascade=2))
