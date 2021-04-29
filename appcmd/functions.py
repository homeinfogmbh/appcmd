"""Common functions."""

from contextlib import suppress
from ipaddress import IPv4Network, ip_address
from json import loads
from typing import Union

from flask import request

from hwdb import Deployment, OpenVPN, System, WireGuard
from mdb import Address
from wsgilib import Error


__all__ = [
    'get_json',
    'get_system',
    'get_deployment',
    'get_customer',
    'get_address',
    'get_lpt_address'
]


INTRANET = IPv4Network('10.200.200.0/24')


def get_json() -> Union[dict, list]:
    """Returns POSTed JSON data.

    TODO: This is a hack as long as the Flash Application
    does not send "ContentType: application/json".
    """

    return loads(request.get_data(as_text=True))


def get_system_by_ip() -> System:
    """Returns the system by its source IP address."""

    address = ip_address(request.remote_addr)
    return System.select(cascade=True).where(
        (OpenVPN.ipv4address == address)
        | (WireGuard.ipv4address == address)
    ).get()


def get_system_by_args() -> System:
    """Returns the respective system."""

    if ip_address(request.remote_addr) not in INTRANET:
        raise Error('Can only query system by ID from within the intranet.')

    try:
        system = int(request.args['system'])
    except KeyError:
        raise Error('No system ID specified.') from None
    except ValueError:
        raise Error('System ID is not an integer.') from None

    try:
        return System.select(cascade=True).where(System.id == system).get()
    except System.DoesNotExist:
        raise Error('No such system.', status=404) from None


def get_system(private: bool = True) -> System:
    """Returns the respective system."""

    if private:
        with suppress(System.DoesNotExist):
            return get_system_by_ip()

    return get_system_by_args()


def get_deployment(private: bool = True) -> Deployment:
    """Returns the respective deployment."""

    deployment = get_system(private=private).deployment

    if deployment is None:
        raise Error('System is not deployed.')

    return deployment


def get_customer(private: bool = True) -> Deployment:
    """Returns the respective customer."""

    return get_deployment(private=private).customer


def get_address(private: bool = True) -> Address:
    """Returns the respective address."""

    return get_deployment(private=private).address


def get_lpt_address(private: bool = True) -> Address:
    """Returns the address for local public transport."""

    deployment = get_system(private=private).dataset

    if deployment is None:
        deployment = get_deployment(private=private)

    return deployment.lpt_address or deployment.address
