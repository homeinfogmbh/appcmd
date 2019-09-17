"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_system


__all__ = ['get_departures']


def get_departures():
    """Returns stops for the respective system."""

    system = get_system()
    deployment = system.deployment

    if deployment is None:
        return ('System is not deployed.', 400)

    address = deployment.lpt_address or deployment.address
    return get_response(address)
