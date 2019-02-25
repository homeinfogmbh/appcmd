"""Common functions."""

from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from tarfile import open as TarFile, TarInfo
from tempfile import TemporaryFile

from flask import make_response, request

from mdb import Customer
from mimeutil import FileMetaData
from terminallib import Terminal
from wsgilib import Error

from appcmd.logger import LOGGER


__all__ = [
    'get_json',
    'get_customer',
    'get_terminal',
    'get_customer_and_address',
    'street_houseno',
    'make_attachment',
    'changed_files',
    'tar_files']


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


def make_attachment(bytes_):
    """Returns the respective attachment's name."""

    return (FileMetaData.from_bytes(bytes_).filename, bytes_)


def changed_files(files):
    """Yields files for the respective
    terminal that have changed.
    """

    sha256sums = frozenset(request.json or ())
    manifest = []

    for filename, bytes_ in files:
        sha256sum = sha256(bytes_).hexdigest()
        manifest.append(filename)

        if sha256sum in sha256sums:
            LOGGER.info('Skipping unchanged file: %s.', filename)
            continue

        yield (filename, bytes_)

    yield ('manifest.json', dumps(manifest).encode())


def tar_files(files):
    """Adds the respective files to a tar archive."""

    with TemporaryFile(mode='w+b') as tmp:
        with TarFile(mode='w:xz', fileobj=tmp) as tar:
            empty = True

            for filename, bytes_ in changed_files(files):
                empty = False
                tarinfo = TarInfo(filename)
                tarinfo.size = len(bytes_)
                file = BytesIO(bytes_)
                tar.addfile(tarinfo, file)

        if empty:
            return ('Nothing to do.', 304)

        tmp.flush()
        tmp.seek(0)
        response = make_response(tmp.read())
        response.headers.set('Content-Type', 'application/x-xz')
        return response
