"""Cleaning submission and retrieval."""

from flask import request

from cleaninglog import make_response, CleaningUser, CleaningDate
from wsgilib import Error

from appcmd.functions import get_json, get_system


__all__ = ['list_cleanings', 'add_cleaning']


def list_cleanings():
    """Lists cleaning entries for the respective system."""

    system = get_system()
    deployment = system.deployment

    if deployment is None:
        raise Error('System is not deployed.')

    try:
        limit = int(request.args['limit'])
    except KeyError:
        limit = 10
    else:
        limit = limit or None

    return make_response(CleaningDate.by_deployment(deployment, limit=limit))


def add_cleaning():
    """Adds a cleaning entry."""

    system = get_system()
    deployment = system.deployment

    if deployment is None:
        return ('System is not deployed.', 400)

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
