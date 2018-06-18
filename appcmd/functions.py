"""WSGI handlers for appcmd."""

from urllib.parse import urlparse

from flask import request, Response
from requests import ConnectionError as HTTPConnectionError, get

from aha import LocationNotFound, AhaDisposalClient
from digsigdb import Command, Statistics, CleaningUser, CleaningDate, \
    TenantMessage, DamageReport, ProxyHost
from homeinfo.crm import Customer
from peeweeplus import FieldValueError, FieldNotNullable, InvalidKeys
from terminallib import Terminal
from wsgilib import Error, JSON, PostData

from appcmd.config import MAX_MSG_SIZE
from appcmd.mail import CouldNotSendMail, ContactFormEmail, ContactFormMailer

__all__ = [
    'list_cleanings',
    'garbage_collection',
    'send_contact_mail',
    'tenant2tenant',
    'damage_report',
    'add_statistics',
    'add_cleaning',
    'proxy']


MAILER = ContactFormMailer()
AHA_CLIENT = AhaDisposalClient()
DATA = PostData()
NO_ADDRESS = Error('Terminal has no address.')


def get_customer():
    """Returns the respective customer."""

    try:
        return Customer.get(Customer.id == request.args['cid'])
    except Customer.DoesNotExist:
        raise Error('No such customer.', status=404)


def get_terminal():
    """Returns the respective terminal."""

    try:
        return Terminal.by_ids(request.args['cid'], request.args['tid'])
    except Terminal.DoesNotExist:
        raise Error('No such terminal.', status=404)


def street_houseno():
    """Returns street and house number."""

    try:
        return (request.args['street'], request.args['house_number'])
    except KeyError:
        terminal = get_terminal()

        try:
            address = terminal.location.address
        except AttributeError:
            raise Error('No address specified and terminal has no address.')

        return (address.street, address.house_number)


def send_contact_mail():
    """Sends contact form emails."""

    email = ContactFormEmail.from_dict(DATA.json)

    try:
        return MAILER.send_email(email)
    except CouldNotSendMail:
        raise Error('Could not send email.', status=500)


def tenant2tenant(maxlen=MAX_MSG_SIZE):
    """Stores tenant info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        raise Error('Maximum text length exceeded.', status=413)

    terminal = get_terminal()

    try:
        record = TenantMessage.from_terminal(terminal, message)
    except AttributeError:
        raise NO_ADDRESS

    record.save()
    return ('Tenant message added.', 201)


def damage_report():
    """Stores damage reports."""

    terminal = get_terminal()

    try:
        record = DamageReport.from_terminal(terminal, DATA.json)
    except AttributeError:
        raise NO_ADDRESS
    except InvalidKeys as invalid_keys:
        raise Error('Invalid keys: {}.'.format(invalid_keys.invalid_keys))
    except FieldNotNullable as field_not_nullable:
        raise Error('Field "{}" is not nullable.'.format(
            field_not_nullable.field))
    except FieldValueError as field_value_error:
        raise Error('Invalid value for field "{}": "{}".'.format(
            field_value_error.field, field_value_error.value))

    record.save()
    return ('Damage report added.', 201)


def add_statistics():
    """Adds a new statistics entry."""

    Statistics.add(
        get_customer(), request.args['vid'], request.args.get('tid'),
        request.args['document'])
    return ('Statistics added.', 201)


def list_cleanings():
    """Lists cleaning entries for the respective terminal."""

    terminal = get_terminal()

    try:
        address = terminal.location.address
    except AttributeError:
        raise Error('Terminal has no address.')

    return JSON([
        cleaning_date.to_dict(short=True) for cleaning_date in
        CleaningDate.by_address(address, limit=10)])


def garbage_collection():
    """Returns information about the garbage collection."""

    try:
        pickups = tuple(AHA_CLIENT.by_street_houseno(*street_houseno()))
    except HTTPConnectionError:
        return ('Could not connect to AHA API.', 503)
    except LocationNotFound:
        return ('Location not found.', 404)

    return JSON([pickup.to_dict() for pickup in pickups])


def complete_command():
    """Completes the provided command."""

    customer = get_customer()
    result = False

    for command in Command.select().where(
            (Command.customer == customer)
            & (Command.vid == request.args['vid'])
            & (Command.task == request.args['task'])
            & (Command.completed >> None)):
        command.complete()
        result = True

    return str(int(result))


def add_cleaning():
    """Adds a cleaning entry."""

    terminal = get_terminal()

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args['pin']) &
            (CleaningUser.customer == terminal.customer))
    except CleaningUser.DoesNotExist:
        return ('Invalid PIN.', 403)

    try:
        address = terminal.location.address
    except AttributeError:
        return ('Terminal has no address.', 400)

    CleaningDate.add(user, address)
    return ('Cleaning date added.', 201)


def proxy():
    """Proxies URLs."""

    url = urlparse(request.get_data().decode())

    if url.scheme not in ('http', 'https'):
        return ('Scheme must be HTTP or HTTPS.', 400)
    elif not url.hostname:
        return ('Host name must not be empty.', 400)

    try:
        ProxyHost.get(ProxyHost.hostname == url.hostname)
    except ProxyHost.DoesNotExist:
        return ('Host name is not whitelisted.', 403)

    reply = get(url.geturl())
    return Response(
        reply.content, status=reply.status_code,
        content_type=reply.headers['Content-Type'])
