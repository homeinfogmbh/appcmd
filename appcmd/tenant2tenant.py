"""Tenant-to-tenant messaging."""

from flask import request

from tenant2tenant import email, TenantMessage

from appcmd.config import CONFIG
from appcmd.functions import get_system


__all__ = ['tenant2tenant']


CONFIG_SECTION = CONFIG['TenantToTenant']
MAX_MSG_SIZE = int(CONFIG_SECTION.get('max_msg_size', 2048))


def tenant2tenant(private=False, maxlen=MAX_MSG_SIZE):
    """Stores tenant info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        return ('Maximum text length exceeded.', 413)

    system = get_system(private=private)

    try:
        record = TenantMessage.from_system(system, message)
    except AttributeError:
        return ('System has no address.', 400)

    record.save()
    email(record)
    return ('Tenant message added.', 201)
