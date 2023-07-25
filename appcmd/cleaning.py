"""Cleaning submission and retrieval."""

from typing import Union

from flask import request

from cleaninglog import by_deployment, CleaningUser, CleaningDate
from wsgilib import JSON, XML

from appcmd.functions import get_json, get_deployment, parse_datetime


__all__ = ["list_cleanings", "add_cleaning"]


def list_cleanings() -> Union[JSON, XML]:
    """Lists cleaning entries for the respective system."""

    return by_deployment(get_deployment())


def add_cleaning() -> tuple[str, int]:
    """Adds a cleaning entry."""

    deployment = get_deployment()

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args["pin"])
            & (CleaningUser.customer == deployment.customer)
        )
    except CleaningUser.DoesNotExist:
        return "Invalid PIN.", 403

    try:
        json = get_json()
    except ValueError:
        json = {}

    if (user_timestamp := json.get("userTimestamp")) is not None:
        user_timestamp = parse_datetime(user_timestamp)

    CleaningDate.add(
        user,
        deployment,
        annotations=json.get("annotations"),
        user_timestamp=user_timestamp,
    )
    return "Cleaning date added.", 201
