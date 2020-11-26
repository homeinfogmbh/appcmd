"""Garbage collection info retrieval."""

from typing import Iterable, Tuple

from flask import Response
from requests import ConnectionError as ConnectionError_

from aha import LocationNotFound, AhaDisposalClient, PickupSolution
from wsgilib import ACCEPT, JSON, XML

from appcmd import dom
from appcmd.functions import get_address


__all__ = ['garbage_collection']


AHA_CLIENT = AhaDisposalClient()
Solutions = dom.garbage_collection.solutions.typeDefinition()


def _to_dom(solutions_: Iterable[PickupSolution]) -> Solutions:
    """Returns an XML or JSON response."""

    solutions = dom.garbage_collection.solutions()

    for location_, pickups in solutions_:
        location = dom.garbage_collection.Location()
        location.code = location_.code
        location.street = location_.street
        location.houseNumber = location_.house_number
        location.district = location_.district

        for pickup_ in pickups:
            pickup = dom.garbage_collection.Pickup()
            pickup.interval = pickup_.interval
            pickup.imageLink = pickup_.image_link
            pickup.type = pickup_.type
            pickup.weekday = pickup_.weekday

            for pickup_date_ in pickup_.next_dates:
                pickup_date = dom.garbage_collection.PickupDate(
                    pickup_date_.date)
                pickup_date.exceptional = pickup_date_.exceptional
                pickup_date.weekday = pickup_date_.weekday
                pickup.date.append(pickup_date)

            location.pickup.append(pickup)

        solutions.location.append(location)

    return solutions


def _response(solutions: Iterable[PickupSolution]) -> Tuple[str, int]:
    """Returns an XML or JSON response."""

    if 'application/xml' in ACCEPT or '*/*' in ACCEPT:
        return XML(_to_dom(solutions))

    if 'application/json' in ACCEPT:
        return JSON([solution.to_json() for solution in solutions])

    return ('Invalid content type.', 406)


def garbage_collection() -> Response:
    """Returns information about the garbage collection."""

    address = get_address()

    try:
        solutions = tuple(AHA_CLIENT.by_street_houseno(
            address.street, address.houseno))
    except ConnectionError_:
        return ('Could not connect to AHA API.', 503)
    except LocationNotFound:
        return ('Location not found.', 404)

    return _response(solutions)
