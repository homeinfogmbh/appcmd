"""Local public transportation API."""

from typing import Union

from lptlib import NoGeoCoordinatesForAddress
from lptlib import get_response
from lptlib import get_max_departures
from lptlib import get_max_stops
from wsgilib import JSON, JSONMessage, XML

from appcmd.functions import get_lpt_address


__all__ = ["get_departures"]


def get_departures() -> Union[JSON, JSONMessage, XML]:
    """Returns stops for the respective system."""

    try:
        return get_response(
            get_lpt_address(), stops=get_max_stops(), departures=get_max_departures()
        )
    except NoGeoCoordinatesForAddress as error:
        return JSONMessage(
            "No geo coordinates for address.", address=error.address, status=404
        )
