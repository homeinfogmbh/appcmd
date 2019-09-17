"""Local public transportation API."""

from pyxb import RequireValidWhenParsing

from lptlib import get_response

from appcmd.functions import get_system


__all__ = ['get_departures']


# XXX: Deactivate all PyXB parsing validation
# because of broken TRIAS APIS from VVS and EFA-BW.
RequireValidWhenParsing(False)


def get_departures():
    """Returns stops for the respective system."""

    system = get_system()
    deployment = system.deployment

    if deployment is None:
        return ('System is not deployed.', 400)

    address = deployment.lpt_address or deployment.address
    return get_response(address)
