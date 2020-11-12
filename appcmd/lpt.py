"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_lpt_address


__all__ = ['get_departures']


def get_departures():
    """Returns stops for the respective system."""

    return get_response(get_lpt_address())
