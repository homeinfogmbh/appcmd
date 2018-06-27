"""Loggs application entity screenshots."""

from datetime import datetime
from functools import wraps
from uuid import UUID

from flask import request

from digsigdb import Screenshot, ScreenshotLog

from appcmd.functions import get_customer_and_address

__all__ = [
    'get_screenshot',
    'add_screenshot',
    'show_screenshot',
    'hide_screenshot']


def with_uuid(function):
    """Converts a string into a UUID."""

    @wraps(function)
    def wrapper(uuid, *args, **kwargs):
        """Calls the wrapped function with the parsed UUID."""
        return function(UUID(uuid), *args, **kwargs)

    return wrapper


@with_uuid
def get_screenshot(entity):
    """Checks whether a screenshot of the respective entity exists."""

    customer, address = get_customer_and_address()

    try:
        Screenshot.fetch(entity, customer, address)
    except Screenshot.DoesNotExist:
        return ('No such entity.', 404)

    return ('Entity exists.', 200)


@with_uuid
def add_screenshot(entity):
    """Adds a screenshot for the respective entity."""

    customer, address = get_customer_and_address()
    Screenshot.add(entity, customer, address, request.get_data())
    return ('Screenshot added.', 201)


@with_uuid
def show_screenshot(entity):
    """Starts to show a screenshot."""

    customer, address = get_customer_and_address()
    ScreenshotLog.add(entity, customer, address)
    return ('Entry added.', 201)


@with_uuid
def hide_screenshot(entity):
    """Stops to show a screenshot."""

    customer, address = get_customer_and_address()

    try:
        ScreenshotLog.close(entity, customer, address)
    except ScreenshotLog.DoesNotExist:
        return ('No pending entry found.', 404)

    return ('Entry closed.', 200)
