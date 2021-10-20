"""Local public transportation API."""

from flask import Response

from lptlib import NoGeoCoordinatesForAddress, get_response
from wsgilib import JSONMessage

from appcmd.functions import get_lpt_address


__all__ = ['get_departures']


def get_departures() -> Response:
    """Returns stops for the respective system."""

    try:
        return get_response(get_lpt_address())
    except NoGeoCoordinatesForAddress as error:
        return JSONMessage('No geo coordinates for address.',
                           address=error.address, status=404)
