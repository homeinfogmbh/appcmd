"""Common functions."""

from contextlib import suppress
from datetime import datetime, timezone
from ipaddress import IPv4Address
from ipaddress import IPv6Address
from ipaddress import IPv4Network
from ipaddress import IPv6Network
from ipaddress import ip_address
from json import loads
from typing import Union

from flask import request

from hwdb import Deployment, OpenVPN, System
from mdb import Address
from wsgilib import Error


__all__ = [
    'get_json',
    'get_system',
    'get_deployment',
    'get_customer',
    'get_address',
    'get_lpt_address',
    'parse_datetime'
]


INTRANET_IPV4 = IPv4Network('10.200.200.0/24')
INTRANET_IPV6 = IPv6Network('fdbc:83e9:4512:ea57::/64')


def is_intranet(ip_addr: Union[IPv4Address, IPv6Address]) -> bool:
    """Checks whether the IP address is within the intranet."""

    if isinstance(ip_addr, IPv4Address):
        return ip_addr in INTRANET_IPV4

    if isinstance(ip_addr, IPv6Address):
        return ip_addr in INTRANET_IPV6

    raise TypeError('ip_addr must be IPv4Address or IPv6Address.')


def get_json() -> Union[dict, list]:
    """Returns POSTed JSON data.

    TODO: This is a hack as long as the Flash Application
    does not send "ContentType: application/json".
    """

    return loads(request.get_data(as_text=True))


def get_system_by_ip() -> System:
    """Returns the system by its source IP address."""

    address = ip_address(request.remote_addr)

    if isinstance(address, IPv4Address):
        condition = OpenVPN.ipv4address == address
    elif isinstance(address, IPv6Address):
        condition = System.ipv6address == address
    else:
        raise TypeError('Unexpected IP type:', type(address))

    return System.select(cascade=True).where(condition).get()


def get_system_by_args() -> System:
    """Returns the respective system."""

    if not is_intranet(ip_address(request.remote_addr)):
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


def get_system() -> System:
    """Returns the respective system."""

    with suppress(System.DoesNotExist):
        return get_system_by_ip()

    return get_system_by_args()


def get_deployment() -> Deployment:
    """Returns the respective deployment."""

    if (deployment := get_system().deployment) is None:
        raise Error('System is not deployed.')

    return deployment


def get_customer() -> Deployment:
    """Returns the respective customer."""

    return get_deployment().customer


def get_address() -> Address:
    """Returns the respective address."""

    return get_deployment().address


def get_lpt_address() -> Address:
    """Returns the address for local public transport."""

    system = get_system()
    deployment = system.dataset or system.deployment
    return deployment.lpt_address or deployment.address


def parse_datetime(string: str) -> datetime:
    """Parse a datetime."""

    if string.endswith('Z'):
        return datetime.fromisoformat(string[:-1]).replace(
            tzinfo=timezone.utc).astimezone(None)

    return datetime.fromisoformat(string)
