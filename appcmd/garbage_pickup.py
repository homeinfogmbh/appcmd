"""Garbage collection info retrieval."""

from datetime import date
from typing import Union

from aha import AmbiguousLocations
from aha import HTTPError
from aha import NoLocationFound
from aha import ScrapingError
from aha import find_location
from aha import get_pickups
from aha import Location
from aha import Pickup
from wsgilib import JSON, JSONMessage

from appcmd.functions import get_address


__all__ = ['garbage_pickup']


CACHE = {}


def get_cached_pickups(location: Location, house_number: str) -> list[Pickup]:
    """Returns cached pickups for the day."""

    try:
        locations = CACHE[date.today()]
    except KeyError:
        CACHE.clear()
        CACHE[date.today()] = locations = {}

    try:
        return locations[location]
    except KeyError:
        locations[location] = pickups = list(
            get_pickups(location, house_number))
        return pickups


def garbage_pickup() -> Union[JSON, JSONMessage]:
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
        pickups = get_cached_pickups(location, address.house_number)
    except HTTPError as error:
        return JSONMessage('HTTP error.', status_code=error.status_code)
    except ScrapingError as error:
        return JSONMessage('Scraping error.', error=error.message)

    return JSON([pickup.to_json() for pickup in pickups])
