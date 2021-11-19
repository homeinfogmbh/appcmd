"""Tenant calendar information."""

from tenantcalendar import events, get_customer_events
from wsgilib import XML

from appcmd.functions import get_customer


__all__ = ['list_events']


def list_events() -> XML:
    """Lists customer events."""

    dom = events()

    for customer_event in get_customer_events(get_customer()):
        dom.event.append(customer_event.to_dom())

    return XML(dom)
