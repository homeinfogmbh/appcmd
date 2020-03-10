"""Cleaning submission and retrieval."""

from flask import request

from cleaninglog import by_deployment, CleaningUser, CleaningDate

from appcmd.functions import get_json, get_deployment


__all__ = ['list_cleanings', 'add_cleaning']


def list_cleanings():
    """Lists cleaning entries for the respective system."""

    return by_deployment(get_deployment())


def add_cleaning():
    """Adds a cleaning entry."""

    deployment = get_deployment()

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args['pin']) &
            (CleaningUser.customer == deployment.customer))
    except CleaningUser.DoesNotExist:
        return ('Invalid PIN.', 403)

    try:
        json = get_json()
    except ValueError:
        annotations = None
    else:
        annotations = json.get('annotations')

    CleaningDate.add(user, deployment, annotations=annotations)
    return ('Cleaning date added.', 201)
