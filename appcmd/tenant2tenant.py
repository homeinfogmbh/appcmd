"""Tenant-to-tenant messaging."""

from datetime import datetime
from typing import Optional

from flask import request

from tenant2tenant import email, Configuration, TenantMessage

from appcmd.config import get_config
from appcmd.functions import get_deployment


__all__ = ['tenant2tenant']


def tenant2tenant(maxlen: Optional[int] = None) -> tuple[str, int]:
    """Stores tenant info."""

    maxlen = maxlen or get_config().getint(
        'TenantToTenant', 'max_msg_size', fallback=2048
    )

    try:
        message = request.get_data().decode()
    except UnicodeDecodeError:
        return 'Non-UTF-8 text provided. Refusing.', 415

    if not message:
        return 'Refusing to add empty message.', 406

    if len(message) > maxlen:
        return 'Maximum text length exceeded.', 413

    deployment = get_deployment()
    record = TenantMessage.from_deployment(deployment, message)
    configuration = Configuration.for_customer(deployment.customer)

    if configuration.auto_release:
        record.released = True
        record.start_date = now = datetime.now()
        record.end_date = now + configuration.release_time

    record.save()
    email(record)
    return 'Tenant message added.', 201
