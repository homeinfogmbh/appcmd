"""Digital signage client update server."""

from hashlib import sha256
from pathlib import Path

from flask import request

from wsgilib import Binary

from appcmd.config import CONFIG


__all__ = ['update']


def update():
    """Returns an update, iff available."""

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

    print('Version sent:  ', current_sha256sum, flush=True)
    print('Latest version:', latest_sha256sum, flush=True)

    if latest_sha256sum == current_sha256sum:
        return ('', 204)

    return Binary(digsigclt)
