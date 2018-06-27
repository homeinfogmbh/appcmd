"""Loggs application entity screenshots."""

from uuid import UUID

from flask import request

from digsigdb import Screenshot, ScreenshotLog
from wsgilib import Error

from appcmd.functions import get_customer_and_address

__all__ = [
    'get_screenshot',
    'add_screenshot',
    'show_screenshot',
    'hide_screenshot']


def get_entity():
    """Returns the respective entity UUID."""

    try:
        return UUID(request.args['entity'])
    except KeyError:
        raise Error('No entity UUID specified.')
    except ValueError:
        raise Error('Invalid entity UUID specified.')


def get_screenshot():
    """Checks whether a screenshot of the respective entity exists."""

    customer, address = get_customer_and_address()

    try:
        Screenshot.fetch(get_entity(), customer, address)
    except Screenshot.DoesNotExist:
        return ('No such entity.', 404)

    return ('Entity exists.', 200)


def add_screenshot():
    """Adds a screenshot for the respective entity."""

    customer, address = get_customer_and_address()
    Screenshot.add(get_entity(), customer, address, request.get_data())
    return ('Screenshot added.', 201)


def show_screenshot():
    """Starts to show a screenshot."""

    customer, address = get_customer_and_address()
    ScreenshotLog.add(get_entity(), customer, address)
    return ('Entry added.', 201)


def hide_screenshot():
    """Stops to show a screenshot."""

    customer, address = get_customer_and_address()

    try:
        ScreenshotLog.close(get_entity(), customer, address)
    except ScreenshotLog.DoesNotExist:
        return ('No pending entry found.', 404)

    return ('Entry closed.', 200)
