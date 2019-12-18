"""Digital signage client update server."""

from hashlib import sha256
from pathlib import Path

from flask import request

from wsgilib import Binary

from appcmd.config import CONFIG


__all__ = ['update']


NO_UPDATE_AVAILABLE = ('', 204)


def update_digsigclt():
    """Returns an update of the digital signage client iff available."""

    try:
        path = Path(CONFIG['digsigclt']['path'])
    except (KeyError, TypeError, ValueError):
        return ('File path not configured on server.', 500)

    try:
        with path.open('rb') as file:
            digsigclt = file.read()
    except FileNotFoundError:
        return ('Latest file not found on server.', 500)

    latest_sha256sum = sha256(digsigclt).hexdigest()

    try:
        current_sha256sum = request.get_data().decode()
    except (TypeError, AttributeError, ValueError):
        return ('Did not receive a proper SHA-256 sum.', 400)

    if latest_sha256sum == current_sha256sum:
        return NO_UPDATE_AVAILABLE

    return Binary(digsigclt)


def update_application():
    """Returns an update of the digital
    signage Flash application iff available.
    """

    raise NotImplementedError()


def update_h5ds():
    """Returns an update of the digital
    signage HTML5 application iff available.
    """

    raise NotImplementedError()


def update(target='digsigclt'):
    """Returns an update, iff available."""

    if target == 'digsigclt':
        return update_digsigclt()

    if target == 'application':
        return update_application()

    if target == 'h5ds':
        return update_h5ds()

    return ('Invalid target specified.', 400)
