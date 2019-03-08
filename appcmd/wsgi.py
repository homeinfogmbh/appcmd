"""WSGI private routes (VPN)."""

from functools import partial

from wsgilib import Application

from appcmd.cleaning import list_cleanings, add_cleaning
from appcmd.command import list_commands, complete_command
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
    ('GET', '/cleaning', partial(list_cleanings, private=True),
     'list_cleanings'),
    ('GET', '/garbage_collection', partial(garbage_collection, private=True),
     'garbage_collection'),
    ('GET', '/lpt', partial(get_departures, private=True), 'get_departures'),
    ('POST', '/cleaning', partial(add_cleaning, private=True), 'add_cleaning'),
    ('POST', '/contactform', send_contact_mail, 'send_contact_mail'),
    ('POST', '/damagereport', partial(damage_report, private=True),
     'damage_report'),
    ('POST', '/poll', cast_vote, 'cast_vote'),
    ('POST', '/proxy', partial(proxy, private=True), 'proxy'),
    ('POST', '/statistics', partial(add_statistics, private=True),
     'add_statistics'),
    ('POST', '/tenant2tenant', partial(tenant2tenant, private=True),
     'tenant2tenant'))
PUBLIC_ROUTES = (
    ('GET', '/command', list_commands, 'list_commands'),
    ('POST', '/command', complete_command, 'complete_command'),
    ('POST', '/statistics', partial(add_statistics, private=False),
     'add_statistics'),
    ('POST', '/proxy', partial(proxy, private=False), 'proxy'))
PRIVATE.add_routes(PRIVATE_ROUTES)
PUBLIC.add_routes(PUBLIC_ROUTES)
