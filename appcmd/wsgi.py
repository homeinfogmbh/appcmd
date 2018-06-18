"""WSGI handlers for appcmd."""

from wsgilib import Application

from appcmd.functions import list_cleanings, garbage_collection, \
    send_contact_mail, tenant2tenant, damage_report, add_statistics, \
    add_cleaning, proxy

__all__ = ['PRIVATE']


PRIVATE = Application('private', cors=True, debug=True)
PUBLIC = Application('public', cors=True, debug=True)
INVALID_OPERATION = ('Invalid operation.', 400)


@PRIVATE.route('/<command>', methods=['GET'])
def get_private(command):
    """Handles public get request."""

    if command == 'cleaning':
        return list_cleanings()
    elif command == 'garbage_collection':
        return garbage_collection()

    return INVALID_OPERATION


@PRIVATE.route('/<command>', methods=['POST'])
def post_private(command):
    """Handles private POST request."""

    if command == 'contactform':
        return send_contact_mail()
    elif command == 'tenant2tenant':
        return tenant2tenant()
    elif command == 'damagereport':
        return damage_report()
    elif command == 'statistics':
        return add_statistics()
    elif command == 'cleaning':
        return add_cleaning()
    elif command == 'proxy':
        return proxy()

    return INVALID_OPERATION


@PUBLIC.route('/<command>', methods=['POST'])
def post_public(command):
    """Handles private POST request."""

    if command == 'statistics':
        return add_statistics()
    elif command == 'proxy':
        return proxy()

    return INVALID_OPERATION
