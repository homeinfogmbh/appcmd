"""WSGI private routes (VPN)."""

from functools import partial

from wsgilib import Application

from appcmd.cleaning import list_cleanings, add_cleaning
from appcmd.damage_report import damage_report
from appcmd.garbage_collection import garbage_collection
from appcmd.lpt import get_departures
from appcmd.mail import send_contact_mail
from appcmd.poll import cast_vote
from appcmd.proxy import proxy
from appcmd.statistics import add_statistics
from appcmd.tenant2tenant import tenant2tenant


__all__ = ['PRIVATE', 'PUBLIC']


PRIVATE = Application('private', cors=True, debug=True)
PUBLIC = Application('public', cors=True)
PRIVATE_ROUTES = (
    ('GET', '/cleaning', partial(list_cleanings, private=True)),
    ('GET', '/garbage_collection', partial(garbage_collection, private=True)),
    ('GET', '/lpt', partial(get_departures, private=True)),
    ('POST', '/cleaning', partial(add_cleaning, private=True)),
    ('POST', '/contactform', send_contact_mail),
    ('POST', '/damagereport', partial(damage_report, private=True)),
    ('POST', '/poll', cast_vote),
    ('POST', '/proxy', partial(proxy, private=True)),
    ('POST', '/statistics', add_statistics),
    ('POST', '/tenant2tenant', partial(tenant2tenant, private=True))
)
PUBLIC_ROUTES = (('POST', '/proxy', partial(proxy, private=False)),)
PRIVATE.add_routes(PRIVATE_ROUTES)
PUBLIC.add_routes(PUBLIC_ROUTES)
