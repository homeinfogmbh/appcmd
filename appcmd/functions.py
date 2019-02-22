"""Common functions."""

from hashlib import sha256
from json import dumps, loads

from flask import request

from mdb import Customer
from terminallib import Terminal
from wsgilib import Error

from appcmd.logger import LOGGER


__all__ = [
    'get_json',
    'get_customer',
    'get_terminal',
    'get_customer_and_address',
    'street_houseno',
    'changed_files']


def get_json():
    """Returns POSTed JSON data.

    TODO: This is a hack as long as the Flash Application
    does not send "ContentType: application/json".
    """

    return loads(request.get_data(as_text=True))


def get_customer():
    """Returns the respective customer."""

    try:
        return Customer.get(Customer.id == request.args['cid'])
    except Customer.DoesNotExist:
        raise Error('No such customer.', status=404)


def get_terminal():
    """Returns the respective terminal."""

    try:
        return Terminal.by_ids(request.args['cid'], request.args['tid'])
    except Terminal.DoesNotExist:
        raise Error('No such terminal.', status=404)


def get_customer_and_address():
    """Returns customer and address by
    the respective terminal arguments.
    """

    terminal = get_terminal()
    address = terminal.address

    if address is None:
        raise Error('Terminal has no address.')

    return (terminal.customer, address)


def street_houseno():
    """Returns street and house number."""

    try:
        return (request.args['street'], request.args['house_number'])
    except KeyError:
        address = get_terminal().address

        if address is None:
            raise Error('No address specified and terminal has no address.')

        return (address.street, address.house_number)


def changed_files(files):
    """Yields files for the respective
    terminal that have changed.
    """

    sha256sums = request.json or ()
    print('DEBUG:' sha256sums, flush=True)
    manifest = set()
    processed = set()

    for filename, bytes_ in files:
        sha256sum = sha256(bytes_).hexdigest()
        manifest.add(sha256sum)

        if sha256sum in sha256sums:
            LOGGER.info('Skipping unchanged file: %s.', filename)
            continue

        processed.add(sha256sum)
        yield (filename, bytes_)

    if processed:
        manifest = dumps(tuple(manifest)).encode()
        yield ('manifest.json', manifest)
