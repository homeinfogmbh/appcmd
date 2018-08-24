"""Cleaning submission and retrieval."""

from flask import request

from digsigdb import CleaningUser, CleaningDate
from wsgilib import Error, JSON, XML

from appcmd import dom
from appcmd.functions import get_terminal


__all__ = ['list_cleanings', 'add_cleaning']


def _response(cleaning_dates):
    """Creates a response from the respective dictionary."""

    if 'xml' in request.args:
        cleanings = dom.cleaning.cleanings()

        for cleaning_date in cleaning_dates:
            cleaning = dom.cleaning.Cleaning()
            cleaning.timestamp = cleaning_date.timestamp
            user_ = cleaning_date.user
            user = dom.cleaning.User(user_.name)
            user.type = user_.type_
            cleaning.user = user
            cleanings.cleaning.append(cleaning)

        return XML(cleanings)

    return JSON([
        cleaning_date.to_json(short=True) for cleaning_date in cleaning_dates])


def list_cleanings():
    """Lists cleaning entries for the respective terminal."""

    address = get_terminal().address

    if address is None:
        raise Error('Terminal has no address.')

    return _response(CleaningDate.by_address(address, limit=10))


def add_cleaning():
    """Adds a cleaning entry."""

    terminal = get_terminal()

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args['pin']) &
            (CleaningUser.customer == terminal.customer))
    except CleaningUser.DoesNotExist:
        return ('Invalid PIN.', 403)

    address = terminal.address

    if address is None:
        return ('Terminal has no address.', 400)

    CleaningDate.add(user, address)
    return ('Cleaning date added.', 201)
