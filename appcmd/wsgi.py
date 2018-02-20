"""WSGI handlers for appcmd."""

from urllib.parse import urlparse

from flask import request, Response
from requests import ConnectionError as HTTPConnectionError, get

from aha import LocationNotFound, AhaDisposalClient
from homeinfo.crm import Customer
from terminallib import Terminal
from wsgilib import Error, JSON, PostData, Application

from appcmd.mail import CouldNotSendMail, ContactFormEmail, ContactFormMailer
from appcmd.orm import Command, Statistics, CleaningUser, CleaningDate, \
    TenantMessage, DamageReport, ProxyHost

__all__ = ['PUBLIC', 'PRIVATE']


MAILER = ContactFormMailer()
AHA_CLIENT = AhaDisposalClient()
PUBLIC = Application('public', cors=True, debug=True)
PRIVATE = Application('private', cors=True, debug=True)
DATA = PostData()


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

        if terminal.location is not None:
            address = terminal.location.address
            return (address.street, address.house_number)

        raise Error('No address specified and terminal has no address.')


def send_contact_mail():
    """Sends contact form emails."""

    email = ContactFormEmail.from_dict(DATA.json)

    try:
        msg = MAILER.send_email(email)
    except CouldNotSendMail:
        raise Error('Could not send email.', status=500)

    return msg


def tenant2tenant(maxlen=2048):
    """Stores tenant info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        raise Error('Maximum text length exceeded.', status=413)

    TenantMessage.add(get_terminal(), message)
    return ('Tenant message added.', 201)


def damage_report():
    """Stores damage reports."""

    try:
        DamageReport.from_dict(get_terminal(), DATA.json)
    except KeyError as key_error:
        raise Error('Missing property: {}.'.format(key_error.args[0]))

    return ('Damage report added.', 201)


def add_statistics():
    """Adds a new statistics entry."""

    Statistics.add(
        get_customer(), request.args['vid'], request.args.get('tid'),
        request.args['document'])
    return ('Statistics added.', 201)


def list_commands():
    """Lists commands for the respective terminal."""

    customer = get_customer()
    tasks = []

    for command in Command.select().where(
            (Command.customer == customer)
            & (Command.vid == request.args['vid'])
            & (Command.completed >> None)):
        tasks.append(command.task)

    return JSON(tasks)


def list_cleanings():
    """Lists cleaning entries for the respective terminal."""

    terminal = get_terminal()

    try:
        address = terminal.location.address
    except AttributeError:
        raise Error('Terminal has no address.')

    json = CleaningDate.by_address(address, limit=10)
    return JSON(json)


def garbage_collection():
    """Returns information about the garbage collection."""

    try:
        pickup = AHA_CLIENT.by_address(*street_houseno())
    except HTTPConnectionError:
        return ('Could not connect to AHA API.', 503)
    except LocationNotFound:
        return ('Location not found.', 404)

    return JSON(pickup.to_dict())


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


@PRIVATE.route('/<command>', methods=['POST'])
def post_private(command):
    """Handles private POST request."""

    if command == 'contactform':
        return send_contact_mail()
    elif command == 'tenant2tenant':
        return tenant2tenant()
    elif command == 'damagereport':
        return damage_report()
    elif command == 'statistics':
        return add_statistics()

    return ('Invalid operation.', 400)


@PUBLIC.route('/<command>')
def get_public(command):
    """Handles public get request."""

    if command == 'command':
        return list_commands()
    elif command == 'cleaning':
        return list_cleanings()
    elif command == 'garbage_collection':
        return garbage_collection()

    return ('Invalid operation.', 400)


@PUBLIC.route('/<command>', methods=['POST'])
def post_public(command):
    """Handles public POST request."""

    if command == 'command':
        return complete_command()
    elif command == 'statistics':
        return add_statistics()
    elif command == 'cleaning':
        return add_cleaning()
    elif command == 'proxy':
        return proxy()

    return ('Invalid operation.', 400)
