"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_terminal


__all__ = ['get_departures']


def get_departures(private=False):
    """Returns stops for the respective terminal."""

    terminal = get_terminal(private=private)
    return get_response(terminal.address)
