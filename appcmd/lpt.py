"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_system


__all__ = ['get_departures']


def get_departures(private=False):
    """Returns stops for the respective terminal."""

    system = get_system(private=private)
    location = system.location

    if location is None:
        return ('System is not located.', 400)

    address = location.lpt_address or location.address
    return get_response(address)
