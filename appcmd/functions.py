"""Common functions."""

from contextlib import suppress
from ipaddress import IPv4Address
from json import loads

from flask import request

from terminallib import OpenVPN, System, WireGuard
from wsgilib import Error


__all__ = [
    'get_json',
    'get_system',
    'get_deployment',
    'get_customer',
    'get_address'
]


def get_json():
    """Returns POSTed JSON data.

    TODO: This is a hack as long as the Flash Application
    does not send "ContentType: application/json".
    """

    return loads(request.get_data(as_text=True))


def get_system_by_ip():
    """Returns the system by its source IP address."""

    address = IPv4Address(request.remote_addr)
    condition = OpenVPN.ipv4address == address
    condition |= WireGuard.ipv4address == address
    select = System.select().join(WireGuard)
    select = select.switch(System).join(OpenVPN)
    return select.where(condition).get()


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


def get_deployment(private=True):
    """Returns the respective deployment."""

    deployment = get_system(private=private).deployment

    if deployment is None:
        raise Error('System is not deployed.')

    return deployment


def get_customer(private=True):
    """Returns the respective customer."""

    return get_deployment(private=private).customer


def get_address(private=True):
    """Returns the respective address."""

    return get_deployment(private=private).address
