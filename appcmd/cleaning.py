"""Cleaning submission and retrieval."""

from flask import request

from digsigdb import CleaningUser, CleaningDate
from wsgilib import Error, JSON, XML

from appcmd import dom
from appcmd.functions import get_terminal


__all__ = ['list_cleanings', 'add_cleaning']


def _cleaning_response(cleaning_dates):
    """Creates a response from the respective dictionary."""

    if 'xml' in request.args:
        cleanings = dom.cleaning.cleanings()

        for cleaning_date in cleaning_dates:
            cleaning_ = dom.cleaning.Cleaning()
            cleaning_.timestamp = cleaning_date.timestamp
            cleaning_.user = cleaning_date.user.name
            cleanings.cleaning.append(cleaning_)

        return XML(cleanings)

    return JSON([
        cleaning_date.to_dict(short=True) for cleaning_date in cleaning_dates])


def list_cleanings():
    """Lists cleaning entries for the respective terminal."""

    terminal = get_terminal()

    try:
        address = terminal.location.address
    except AttributeError:
        raise Error('Terminal has no address.')

    return _cleaning_response(CleaningDate.by_address(address, limit=10))


def add_cleaning():
    """Adds a cleaning entry."""

    terminal = get_terminal()

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args['pin']) &
            (CleaningUser.customer == terminal.customer))
    except CleaningUser.DoesNotExist:
        return ('Invalid PIN.', 403)

    try:
        address = terminal.location.address
    except AttributeError:
        return ('Terminal has no address.', 400)

    CleaningDate.add(user, address)
    return ('Cleaning date added.', 201)
