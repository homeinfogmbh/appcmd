"""WSGI private routes (VPN)."""

from functools import partial

from wsgilib import Application

from appcmd.booking import list_bookables, list_bookings, book, cancel
from appcmd.cleaning import list_cleanings, add_cleaning
from appcmd.damage_report import damage_report
from appcmd.garbage_collection import garbage_collection
from appcmd.lpt import get_departures
from appcmd.mail import send_contact_mail
from appcmd.poll import cast_vote
from appcmd.proxy import proxy
from appcmd.statistics import add_statistics
from appcmd.sysdep import get_deployment
from appcmd.tenant2tenant import tenant2tenant
from appcmd.update import update


__all__ = ['PRIVATE', 'PUBLIC']


PRIVATE = Application('private', cors=True, debug=True)
PUBLIC = Application('public', cors=True)
PRIVATE_ROUTES = (
    ('GET', '/bookables', list_bookables),
    ('GET', '/bookings', list_bookings),
    ('POST', '/bookings', book),
    ('DELETE', '/bookings/<int:ident>', cancel),
    ('GET', '/cleaning', list_cleanings),
    ('GET', '/deployment', get_deployment),
    ('GET', '/garbage_collection', garbage_collection),
    ('GET', '/lpt', get_departures),
    ('POST', '/cleaning', add_cleaning),
    ('POST', '/contactform', send_contact_mail),
    ('POST', '/damagereport', damage_report),
    ('POST', '/poll', cast_vote),
    ('POST', '/proxy', proxy),
    ('POST', '/statistics', add_statistics),
    ('POST', '/tenant2tenant', tenant2tenant),
    ('POST', '/digsigclt', update),     # XXX: Legacy interface.
    ('POST', '/update/<target>', update)
)
PUBLIC_ROUTES = (('POST', '/proxy', partial(proxy, private=False)),)
PRIVATE.add_routes(PRIVATE_ROUTES)
PUBLIC.add_routes(PUBLIC_ROUTES)
