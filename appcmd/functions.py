"""WSGI handlers for appcmd."""

from flask import request

from homeinfo.crm import Customer
from terminallib import Terminal
from wsgilib import Error

__all__ = [
    'get_customer',
    'get_terminal',
    'get_customer_and_address',
    'street_houseno']


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

    try:
        address = terminal.location.address
    except AttributeError:
        raise Error('Terminal has no address.')

    return (terminal.customer, address)


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
