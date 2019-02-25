"""WSGI private routes (VPN)."""

from functools import partial

from wsgilib import Application

from appcmd.cleaning import list_cleanings, add_cleaning
from appcmd.command import list_commands, complete_command
from appcmd.damage_report import damage_report
from appcmd.digsig import get_digsig_pkg
from appcmd.garbage_collection import garbage_collection
from appcmd.lpt import get_departures
from appcmd.mail import send_contact_mail
from appcmd.poll import cast_vote
from appcmd.proxy import proxy
from appcmd.screenshots import add_screenshot
from appcmd.screenshots import get_screenshot
from appcmd.screenshots import hide_screenshot
from appcmd.screenshots import show_screenshot
from appcmd.statistics import add_statistics
from appcmd.tenant2tenant import tenant2tenant


__all__ = ['PRIVATE', 'PUBLIC']


PRIVATE = Application('private', cors=True, debug=True)
PUBLIC = Application('public', cors=True)
PRIVATE_ROUTES = (
    ('GET', '/cleaning', list_cleanings, 'list_cleanings'),
    ('GET', '/garbage_collection', garbage_collection, 'garbage_collection'),
    ('GET', '/lpt', get_departures, 'get_departures'),
    ('GET', '/screenshot', get_screenshot, 'get_screenshot'),
    ('POST', '/cleaning', add_cleaning, 'add_cleaning'),
    ('POST', '/contactform', send_contact_mail, 'send_contact_mail'),
    ('POST', '/damagereport', damage_report, 'damage_report'),
    ('POST', '/digsig', get_digsig_pkg, 'get_digsig_pkg'),
    ('POST', '/poll', cast_vote, 'cast_vote'),
    ('POST', '/proxy', partial(proxy, check_hostname=False), 'proxy'),
    ('POST', '/screenshot', add_screenshot, 'add_screenshot'),
    ('POST', '/statistics', add_statistics, 'add_statistics'),
    ('POST', '/tenant2tenant', tenant2tenant, 'tenant2tenant'),
    ('PUT', '/screenshot', show_screenshot, 'show_screenshot'),
    ('PATCH', '/screenshot', hide_screenshot, 'hide_screenshot'))
PUBLIC_ROUTES = (
    ('GET', '/command', list_commands, 'list_commands'),
    ('POST', '/command', complete_command, 'complete_command'),
    ('POST', '/statistics', add_statistics, 'add_statistics'),
    ('POST', '/proxy', proxy, 'proxy'))
PRIVATE.add_routes(PRIVATE_ROUTES)
PUBLIC.add_routes(PUBLIC_ROUTES)
