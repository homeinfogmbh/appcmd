"""Renting."""

from datetime import datetime

from rentallib import dom
from rentallib import AlreadyRented
from rentallib import EndBeforeStart
from rentallib import DurationTooLong
from rentallib import DurationTooShort
from rentallib import Rentable
from rentallib import Renting
from timelib import strpdatetime
from wsgilib import Error, OK, XML

from appcmd.functions import get_json, get_customer_and_address


__all__ = ['list_rentables', 'list_rentings', 'submit_renting']


def list_rentables():
    """Lists available rentables."""

    customer, _ = get_customer_and_address()
    xml = dom.rentables()

    for rentable in Rentable.select().where(Rentable.customer == customer):
        xml.rentable.append(rentable.to_dom())

    return XML(xml)


def list_rentings():
    """Lists stored rentings."""

    xml = dom.rentings()
    customer, _ = get_customer_and_address()

    for renting in Renting.select().join(Rentable).where(
            (Rentable.customer == customer)
            & (Renting.end >= datetime.now())).order_by(Renting.start):
        xml.renting.append(renting.to_dom())

    return XML(xml)


def submit_renting():   # pylint: disable=R0911
    """Rents a rentable."""

    json = get_json()

    try:
        rentable = json['rentable']
    except KeyError:
        return Error('No rentable specified.')

    try:
        start = strpdatetime(json['start'])
    except KeyError:
        return Error('No start datetime specified.')
    except ValueError:
        return Error('Datetime must be in ISO format.')

    try:
        end = strpdatetime(json['end'])
    except KeyError:
        return Error('No end datetime specified.')
    except ValueError:
        return Error('Datetime must be in ISO format.')

    rentee = json.get('rentee')

    if not rentee:
        return Error('No rentee specified.')

    customer, _ = get_customer_and_address()

    try:
        rentable = Rentable.get(
            (Rentable.id == rentable) & (Rentable.customer == customer))
    except Rentable.DoesNotExist:
        return Error('No such rentable.', status=404)

    try:
        rentable.rent(rentee, start, end)
    except EndBeforeStart:
        return Error('Start date must be before end date.')
    except DurationTooLong:
        return Error('Rent duration is too long.')
    except DurationTooShort:
        return Error('Rent duration is too short.')
    except AlreadyRented:
        return Error('Rentable has already been rented.', status=409)

    return OK(f'{rentable.id}')
