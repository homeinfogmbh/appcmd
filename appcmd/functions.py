"""Common functions."""

from contextlib import suppress
from ipaddress import IPv4Address
from json import loads

from flask import request

from mdb import Customer
from terminallib import OpenVPN, System
from wsgilib import Error


__all__ = [
    'get_json',
    'get_customer',
    'get_system',
    'get_customer_and_address',
    'street_houseno'
]


def get_json():
    """Returns POSTed JSON data.

    TODO: This is a hack as long as the Flash Application
    does not send "ContentType: application/json".
    """

    return loads(request.get_data(as_text=True))


def get_customer():
    """Returns the respective customer."""

    try:
        cid = int(request.args['cid'])
    except KeyError:
        raise Error('No customer ID specified.')
    except ValueError:
        raise Error('Customer ID is not an integer.')

    try:
        return Customer[cid]
    except Customer.DoesNotExist:
        raise Error('No such customer.', status=404)


def get_system_by_ip():
    """Returns the system by its source IP address."""

    address = IPv4Address(request.remote_addr)
    return System.select().join(OpenVPN).where(
        OpenVPN.ipv4address == address).get()


def get_system_by_args():
    """Returns the respective system."""

    try:
        system = int(request.args['system'])
    except KeyError:
        raise Error('No system ID specified.')
    except ValueError:
        raise Error('System ID is not an integer.')

    try:
        return System[system]
    except System.DoesNotExist:
        raise Error('No such system.', status=404)


def get_system(private=True):
    """Returns the respective system."""

    if private:
        with suppress(ValueError, System.DoesNotExist):
            return get_system_by_ip()

    return get_system_by_args()


def get_customer_and_address():
    """Returns customer and address by
    the respective system arguments.
    """

    system = get_system()
    deployment = system.deployment

    if deployment is None:
        raise Error('System is not deployed.')

    return (deployment.customer, deployment.address)


def street_houseno():
    """Returns street and house number."""

    try:
        return (request.args['street'], request.args['house_number'])
    except KeyError:
        deployment = get_system().deployment

        if deployment is None:
            raise Error('No address specified and system is not deployed.')

        return (deployment.address.street, deployment.address.house_number)
