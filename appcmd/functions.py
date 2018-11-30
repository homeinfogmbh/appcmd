"""Common functions."""

from json import loads

from flask import request

from mdb import Customer
from terminallib import Terminal
from wsgilib import Error


__all__ = [
    'get_json',
    'get_customer',
    'get_terminal',
    'get_customer_and_address',
    'street_houseno']


def get_json():
    """Returns POSTed JSON data.

    TODO: This is a hack as long as the Flash Application
    does not send "ContentType: application/json".
    """

    return loads(request.get_data(as_text=True))


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


def get_customer_and_address():
    """Returns customer and address by
    the respective terminal arguments.
    """

    terminal = get_terminal()
    address = terminal.address

    if address is None:
        raise Error('Terminal has no address.')

    return (terminal.customer, address)


def street_houseno():
    """Returns street and house number."""

    try:
        return (request.args['street'], request.args['house_number'])
    except KeyError:
        address = get_terminal().address

        if address is None:
            raise Error('No address specified and terminal has no address.')

        return (address.street, address.house_number)
