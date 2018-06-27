"""Tenant-to-tenant messaging."""

from flask import request

from digsigdb import TenantMessage
from wsgilib import Error

from appcmd.config import MAX_MSG_SIZE
from appcmd.functions import get_terminal

__all__ = ['tenant2tenant']


def tenant2tenant(maxlen=MAX_MSG_SIZE):
    """Stores tenant info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        raise Error('Maximum text length exceeded.', status=413)

    terminal = get_terminal()

    try:
        record = TenantMessage.from_terminal(terminal, message)
    except AttributeError:
        raise Error('Terminal has no address.')

    record.save()
    return ('Tenant message added.', 201)
