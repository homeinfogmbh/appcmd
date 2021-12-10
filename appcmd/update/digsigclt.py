"""Digital signage client update server."""

from pathlib import Path

from flask import Response

from wsgilib import Binary

from appcmd.config import get_config
from appcmd.update.common import FileInfo


__all__ = ['update']


NO_UPDATE_AVAILABLE = ('No update available.', 204)


def update() -> Response:
    """Returns an update of the digital signage client iff available."""

    try:
        path = Path(get_config().get('digsigclt', 'path'))
    except (KeyError, TypeError, ValueError):
        return ('File path not properly configured on server.', 500)

    try:
        latest_file = FileInfo.from_file(path)
    except FileNotFoundError:
        return ('Latest file not found on server.', 500)

    if latest_file > FileInfo.from_request():
        with path.open('rb') as file:
            return Binary(file.read())

    return NO_UPDATE_AVAILABLE
