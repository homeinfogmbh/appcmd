"""Tenant-to-tenant messaging."""

from flask import request

from tenant2tenant import email, TenantMessage

from appcmd.config import CONFIG
from appcmd.functions import get_terminal


__all__ = ['tenant2tenant']


CONFIG_SECTION = CONFIG['TenantToTenant']
MAX_MSG_SIZE = int(CONFIG_SECTION.get('max_msg_size', 2048))


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
    email(record)
    return ('Tenant message added.', 201)
