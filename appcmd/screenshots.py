"""Loggs application entity screenshots."""

from datetime import datetime
from uuid import UUID

from flask import request

from digsigdb import Screenshot, ScreenshotLog

__all__ = [
    'get_screenshot',
    'add_screenshot',
    'show_screenshot',
    'hide_screenshot']


def get_screenshot(entity):
    """Checks whether a screenshot of the respective entity exists."""

    try:
        Screenshot.get(Screenshot.entity == entity)
    except Screenshot.DoesNotExist:
        return ('No such entity.', 404)

    return ('Entity exists.', 200)


def add_screenshot(entity):
    """Adds a screenshot for the respective entity."""

    try:
        Screenshot.get(Screenshot.entity == entity)
    except Screenshot.DoesNotExist:
        screenshot = Screenshot()
        screenshot.entity = UUID(entity)
        screenshot.bytes = request.get_data()
        screenshot.save()
        return ('Screenshot added.', 201)

    return ('Entity exists.', 400)


def show_screenshot(entity):
    """Starts to show a screenshot."""

    entry = ScreenshotLog()
    entry.entity = UUID(entity)
    entry.begin = datetime.now()
    entry.end = None
    entry.save()
    return ('Entry added.', 201)


def hide_screenshot(entity):
    """Stops to show a screenshot."""

    try:
        entry = ScreenshotLog.get(
            (ScreenshotLog.entity == entity)
            & (ScreenshotLog.end >> None))
    except ScreenshotLog.DoesNotExist:
        return ('No pending entry found.', 404)

    entry.end = datetime.now()
    entry.save()
    return ('Entry saved.', 201)
