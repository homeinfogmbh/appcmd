"""Tenant-to-tenant messaging."""

from flask import request

from tenant2tenant import TenantMessage

from appcmd.config import MAX_MSG_SIZE
from appcmd.functions import get_terminal


__all__ = ['tenant2tenant']


def tenant2tenant(maxlen=MAX_MSG_SIZE):
    """Stores tenant info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        return ('Maximum text length exceeded.', 413)

    terminal = get_terminal()

    try:
        record = TenantMessage.from_terminal(terminal, message)
    except AttributeError:
        return ('Terminal has no address.', 400)

    record.save()
    return ('Tenant message added.', 201)
