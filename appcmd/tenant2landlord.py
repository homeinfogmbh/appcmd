"""Tenant-to-tenant messaging."""

from typing import Optional

from flask import request

from tenant2landlord import email, TenantMessage

from appcmd.config import get_config
from appcmd.functions import get_deployment


__all__ = ['tenant2landlord']


def tenant2landlord(maxlen: Optional[int] = None) -> tuple[str, int]:
    """Stores tenant-to-landlord info."""

    maxlen = maxlen or get_config().getint(
        'TenantToLandlord', 'max_msg_size', fallback=2048)
    message = request.get_data().decode()

    if len(message) > maxlen:
        return (f'Maximum text length of {maxlen} exceeded.', 413)

    deployment = get_deployment()
    record = TenantMessage.from_deployment(deployment, message)
    record.save()
    email(record)
    return ('Tenant message added.', 201)
