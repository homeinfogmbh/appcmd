"""Cleaning submission and retrieval."""

from flask import request

from digsigdb import CleaningUser, CleaningDate
from wsgilib import Error, JSON

from appcmd.functions import get_terminal

__all__ = ['list_cleanings', 'add_cleaning']


def list_cleanings():
    """Lists cleaning entries for the respective terminal."""

    terminal = get_terminal()

    try:
        address = terminal.location.address
    except AttributeError:
        raise Error('Terminal has no address.')

    return JSON([
        cleaning_date.to_dict(short=True) for cleaning_date in
        CleaningDate.by_address(address, limit=10)])


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
