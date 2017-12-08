"""WSGI handlers for appcmd."""

from json import loads, dumps
from urllib.parse import urlparse

from flask import request, jsonify, Response
from peewee import DoesNotExist
from requests import ConnectionError as HTTPConnectionError, get

from aha import LocationNotFound, AhaDisposalClient
from homeinfo.crm import Customer
from terminallib import Terminal
from wsgilib import Application

from appcmd.mail import CouldNotSendMail, ContactFormEmail, ContactFormMailer
from appcmd.orm import Command, Statistics, CleaningUser, CleaningDate, \
    TenantMessage, DamageReport, ProxyHost

__all__ = ['PUBLIC', 'PRIVATE']


MAILER = ContactFormMailer()
AHA_CLIENT = AhaDisposalClient()
PUBLIC = Application('public', cors=True, debug=True)
PRIVATE = Application('private', cors=True, debug=True)


def get_customer():
    """Returns the respective customer."""

    return Customer.get(Customer.id == request.args['cid'])


def get_terminal():
    """Returns the respective terminal."""

    return Terminal.by_ids(request.args['cid'], request.args['tid'])


def street_houseno():
    """Returns street and house number."""

    try:
        return (request.args['street'], request.args['house_number'])
    except KeyError:
        terminal = get_terminal()

        if terminal.location is not None:
            address = terminal.location.address
            return (address.street, address.house_number)

        return None

def send_contact_mail():
    """Sends contact form emails."""

    json = loads(request.get_data().decode())
    email = ContactFormEmail.from_dict(json)

    try:
        msg = MAILER.send_email(email)
    except CouldNotSendMail:
        return ('Could not send email.', 500)

    return msg


def tenant2tenant(maxlen=2048):
    """Stores tenant info."""

    message = request.get_data().decode()

    if len(message) > maxlen:
        return ('Maximum text length exceeded.', 413)

    try:
        TenantMessage.add(get_terminal(), message)
    except DoesNotExist:
        return ('No such terminal.', 404)

    return ('Tenant message added.', 201)


def damage_report():
    """Stores damage reports."""

    json = loads(request.get_data().decode())

    try:
        DamageReport.from_dict(get_terminal(), json)
    except DoesNotExist:
        return ('No such terminal.', 404)
    except KeyError as key_error:
        return ('Missing property: {}.'.format(key_error.args[0]), 400)

    return ('Damage report added.', 201)


def add_statistics():
    """Adds a new statistics entry."""

    try:
        Statistics.add(
            get_customer(), request.args['vid'], request.args['tid'],
            request.args['document'])
    except DoesNotExist:
        return ('No such customer.', 404)

    return ('Statistics added.', 201)


def list_commands():
    """Lists commands for the respective terminal."""

    try:
        customer = get_customer()
    except DoesNotExist:
        return ('No such customer.', 404)

    tasks = []

    for command in Command.select().where(
            (Command.customer == customer)
            & (Command.vid == request.args['vid'])
            & (Command.completed >> None)):
        tasks.append(command.task)

    return Response(dumps(tasks), mimetype='application/json')


def list_cleanings():
    """Lists cleaning entries for the respective terminal."""

    try:
        terminal = get_terminal()
    except DoesNotExist:
        return ('No such terminal.', 404)

    try:
        address = terminal.location.address
    except AttributeError:
        return ('Terminal has no address.', 400)

    json = CleaningDate.by_address(address, limit=10)
    return Response(dumps(json), mimetype='application/json')


def garbage_collection():
    """Returns information about the garbage collection."""

    try:
        street, house_number = street_houseno()
    except KeyError:
        return ('Neither street and house_number, not tid and cid '
                'were specified.', 400)
    except DoesNotExist:
        return ('No such terminal.', 404)
    except TypeError:
        return ('Terminal has no address associated.', 400)

    try:
        pickup = AHA_CLIENT.by_address(street, house_number)
    except HTTPConnectionError:
        return ('Could not connect to AHA API.', 503)
    except LocationNotFound:
        return ('Location not found.', 404)

    return jsonify(pickup.to_dict())


def complete_command():
    """Completes the provided command."""

    try:
        customer = get_customer()
    except DoesNotExist:
        return ('No such customer.', 404)

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

    try:
        terminal = get_terminal()
    except DoesNotExist:
        return ('No such terminal.', 404)

    try:
        user = CleaningUser.get(
            (CleaningUser.pin == request.args['pin']) &
            (CleaningUser.customer == terminal.customer))
    except DoesNotExist:
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
    except DoesNotExist:
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
