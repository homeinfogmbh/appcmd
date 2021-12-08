"""Garbage collection info retrieval."""

from typing import Union

from aha import AmbiguousLocations
from aha import HTTPError
from aha import NoLocationFound
from aha import ScrapingError
from aha import find_location
from aha import get_pickups
from wsgilib import JSON, JSONMessage

from appcmd.functions import get_address


__all__ = ['garbage_collection']


def garbage_collection() -> Union[JSON, JSONMessage]:
    """Returns information about the garbage collection."""

    address = get_address()

    try:
        location = find_location(address.street)
    except NoLocationFound:
        return JSONMessage('No matching locations found.')
    except AmbiguousLocations as locations:
        return JSONMessage('Multiple matching locations found.',
                           locations=[l.name for l in locations])

    try:
        pickups = get_pickups(location, address.house_number)
    except HTTPError as error:
        return JSONMessage('HTTP error.', status_code=error.status_code)
    except ScrapingError as error:
        return JSONMessage('Scraping error.', error=error.message)

    return JSON([pickup.to_json() for pickup in pickups])
