"""Tenant-to-tenant messaging."""

from flask import request

from tenant2landlord import email, TenantMessage

from appcmd.config import CONFIG
from appcmd.functions import get_deployment


__all__ = ['tenant2landlord']


MAX_MSG_SIZE = CONFIG.getint('TenantToLandlord', 'max_msg_size', fallback=2048)


def tenant2landlord(maxlen: int = MAX_MSG_SIZE) -> tuple[str, int]:
    """Stores tenant-to-landlord info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        return (f'Maximum text length of {MAX_MSG_SIZE} exceeded.', 413)

    deployment = get_deployment()
    record = TenantMessage.from_deployment(deployment, message)
    record.save()
    email(record)
    return ('Tenant message added.', 201)
