"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_terminal


__all__ = ['get_departures']


def get_departures():
    """Returns stops for the respective terminal."""

    return get_response(get_terminal().address)
