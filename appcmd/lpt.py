"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_system


__all__ = ['get_departures']


def get_departures():
    """Returns stops for the respective system."""

    deployment = get_system().deployment

    if deployment is None:
        return ('System is not deployed.', 400)

    return get_response(deployment.lpt_address or deployment.address)
