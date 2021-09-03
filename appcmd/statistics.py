"""Statistics submission."""

from typing import Tuple

from flask import request

from digsigdb import Statistics

from appcmd.functions import get_deployment


__all__ = ['add_statistics']


def add_statistics() -> Tuple[str, int]:
    """Adds a new statistics entry."""

    try:
        text = request.args['document']
    except KeyError:
        text = request.get_data(as_text=True)

    Statistics.add(get_deployment(), text)
    return ('Statistics added.', 201)
