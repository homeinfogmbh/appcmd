"""WSGI private routes (VPN)."""

from wsgilib import Application

from appcmd.cleaning import list_cleanings, add_cleaning
from appcmd.damage_report import damage_report
from appcmd.garbage_collection import garbage_collection
from appcmd.mail import send_contact_mail
from appcmd.proxy import proxy
from appcmd.screenshots import get_screenshot, add_screenshot, \
    show_screenshot, hide_screenshot
from appcmd.statistics import add_statistics
from appcmd.tenant2tenant import tenant2tenant

__all__ = ['PRIVATE', 'PUBLIC']


PRIVATE = Application('private', cors=True, debug=True)
PUBLIC = Application('public', cors=True, debug=True)
PRIVATE_ROUTES = (
    ('GET', '/cleaning', list_cleanings, 'list_cleanings'),
    ('GET', '/garbage_collection', garbage_collection, 'garbage_collection'),
    ('GET', '/screenshot/<entity>', get_screenshot, 'get_screenshot'),
    ('POST', '/contactform', send_contact_mail, 'send_contact_mail'),
    ('POST', '/tenant2tenant', tenant2tenant, 'tenant2tenant'),
    ('POST', '/damagereport', damage_report, 'damage_report'),
    ('POST', '/statistics', add_statistics, 'add_statistics'),
    ('POST', '/cleaning', add_cleaning, 'add_cleaning'),
    ('POST', '/proxy', proxy, 'proxy'),
    ('POST', '/screenshot/<entity>', add_screenshot, 'add_screenshot'),
    ('PUT', '/screenshot/<entity>', show_screenshot, 'show_screenshot'),
    ('POST', '/screenshot/<entity>', hide_screenshot, 'hide_screenshot'))
PUBLIC_ROUTES = (
    ('POST', '/statistics', add_statistics, 'add_statistics'),
    ('POST', '/proxy', proxy, 'proxy'))
PRIVATE.add_routes(PRIVATE_ROUTES)
PUBLIC.add_routes(PUBLIC_ROUTES)
