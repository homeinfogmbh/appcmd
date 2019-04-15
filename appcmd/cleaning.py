"""Cleaning submission and retrieval."""

from flask import request

from digsigdb import CleaningUser, CleaningDate
from digsigdb.dom import cleanings
from wsgilib import ACCEPT, Error, JSON, XML

from appcmd.functions import get_json, get_system


__all__ = ['list_cleanings', 'add_cleaning']


def _response(cleaning_dates):
    """Creates a response from the respective dictionary."""

    if 'application/json' in ACCEPT or '*/*' in ACCEPT:
        return JSON([
            cleaning_date.to_json(short=True)
            for cleaning_date in cleaning_dates])

    xml = cleanings()

    for cleaning_date in cleaning_dates:
        xml.cleaning.append(cleaning_date.to_dom())

    return XML(xml)


def list_cleanings(private=False):
    """Lists cleaning entries for the respective system."""

    system = get_system(private=private)
    location = system.location

    if location is None:
        raise Error('System is not located.')

    try:
        limit = int(request.args['limit'])
    except KeyError:
        limit = 10
    else:
        limit = limit or None

    return _response(CleaningDate.by_address(location.address, limit=limit))


def add_cleaning(private=False):
    """Adds a cleaning entry."""

    system = get_system(private=private)

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args['pin']) &
            (CleaningUser.customer == system.customer))
    except CleaningUser.DoesNotExist:
        return ('Invalid PIN.', 403)

    location = system.location

    if location is None:
        return ('System is not located.', 400)

    try:
        json = get_json()
    except ValueError:
        annotations = None
    else:
        annotations = json.get('annotations')

    CleaningDate.add(user, location.address, annotations=annotations)
    return ('Cleaning date added.', 201)
