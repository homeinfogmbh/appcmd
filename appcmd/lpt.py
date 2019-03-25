"""Local public transportation API."""

from lptlib import get_response

from appcmd.functions import get_terminal


__all__ = ['get_departures']


def get_departures():
    """Returns stops for the respective terminal."""

    terminal = get_terminal()
    address = terminal.lpt_address or terminal.address
    return get_response()
