"""Digital signage client update server."""

from appcmd.update.application import update as update_application
from appcmd.update.digsigclt import update as update_digsigclt


__all__ = ['update']


def update(target='digsigclt'):
    """Returns an update, iff available."""

    if target == 'digsigclt':
        return update_digsigclt()

    if target == 'application':
        return update_application()

    return ('Invalid target specified.', 400)
