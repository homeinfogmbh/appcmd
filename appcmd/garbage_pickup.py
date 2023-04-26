"""Garbage collection info retrieval."""

from typing import Union

from aha import by_address
from wsgilib import JSON, JSONMessage

from appcmd.functions import get_address


__all__ = ['garbage_pickup']


def garbage_pickup() -> Union[JSON, JSONMessage]:
    """Returns information about the garbage collection."""

    return by_address(get_address())
