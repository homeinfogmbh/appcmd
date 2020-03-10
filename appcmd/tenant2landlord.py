"""Tenant-to-tenant messaging."""

from datetime import datetime

from flask import request

from tenant2landlord import email, Configuration, TenantMessage

from appcmd.config import CONFIG
from appcmd.functions import get_deployment


__all__ = ['tenant2landlord']


CONFIG_SECTION = CONFIG['TenantToLandlord']
MAX_MSG_SIZE = int(CONFIG_SECTION.get('max_msg_size', 2048))


def tenant2landlord(maxlen=MAX_MSG_SIZE):
    """Stores tenant-to-landlord info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        return ('Maximum text length exceeded.', 413)

    deployment = get_deployment()
    record = TenantMessage.from_deployment(deployment, message)
    configuration = Configuration.for_customer(deployment.customer)

    if configuration.auto_release:
        record.released = True
        record.start_date = now = datetime.now()
        record.end_date = now + configuration.release_time

    record.save()
    email(record)
    return ('Tenant message added.', 201)
