"""WSGI private routes (VPN)."""

from wsgilib import Application

from appcmd.booking import list_bookables, list_bookings, book, cancel
from appcmd.cleaning import list_cleanings, add_cleaning
from appcmd.damage_report import damage_report
from appcmd.garbage_pickup import garbage_pickup
from appcmd.logger import init_logger
from appcmd.lpt import get_departures
from appcmd.mail import send_contact_mail
from appcmd.poll import cast_vote
from appcmd.proxy import proxy
from appcmd.statistics import add_statistics
from appcmd.sysdep import deployment_info
from appcmd.tenant2landlord import tenant2landlord
from appcmd.tenant2tenant import tenant2tenant
from appcmd.tenantcalendar import list_events


__all__ = ['PRIVATE', 'PUBLIC']


PRIVATE = Application('private', cors=True)
PUBLIC = Application('public', cors=True)
PRIVATE_ROUTES = [
    ('GET', '/bookables', list_bookables),
    ('GET', '/bookings', list_bookings),
    ('POST', '/bookings', book),
    ('DELETE', '/bookings/<int:ident>', cancel),
    ('GET', '/cleaning', list_cleanings),
    ('GET', '/deployment', deployment_info),
    ('GET', '/garbage-pickup', garbage_pickup),
    ('GET', '/lpt', get_departures),
    ('GET', '/tenantcalendar', list_events),
    ('POST', '/cleaning', add_cleaning),
    ('POST', '/contactform', send_contact_mail),
    ('POST', '/damagereport', damage_report),
    ('POST', '/poll', cast_vote),
    ('POST', '/proxy', proxy),
    ('POST', '/statistics', add_statistics),
    ('POST', '/tenant2landlord', tenant2landlord),
    ('POST', '/tenant2tenant', tenant2tenant)
]
PUBLIC_ROUTES = [('POST', '/proxy', proxy)]
PRIVATE.add_routes(PRIVATE_ROUTES)
PUBLIC.add_routes(PUBLIC_ROUTES)
PRIVATE.before_first_request(init_logger)
PUBLIC.before_first_request(init_logger)
