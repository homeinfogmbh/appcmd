"""Renting."""

from flask import request

from rentallib import dom
from rentallib import AlreadyRented
from rentallib import EndBeforeStart
from rentallib import DurationTooLong
from rentallib import DurationTooShort
from rentallib import Rentable
from rentallib import Renting
from timelib import strpdatetime
from wsgilib import Error, OK

from appcmd.functions import get_customer_and_address


__all__ = ['list_rentables', 'list_rentings', 'submit_rent']


def list_rentables():
    """Lists available rentables."""

    customer, _ = get_customer_and_address()
    xml = dom.rentables()

    for rentable in Rentable.select().where(Rentable.customer == customer):
        xml.rentable.append(rentable.to_dom())

    return xml


def list_rentings():
    """Lists stored rentings."""

    customer, _ = get_customer_and_address()
    xml = dom.rentings()

    for renting in Renting.select().join(Rentable).where(
            Rentable.customer == customer):
        xml.renting.append(renting.to_dom())

    return xml


def submit_rent():
    """Rents a rentable."""

    try:
        rentable = request.json['rentable']
    except KeyError:
        return Error('No rentable specified.')

    try:
        start = strpdatetime(request.json['start'])
    except KeyError:
        return Error('No start datetime specified.')
    except ValueError:
        return Error('Datetime must be in ISO format.')

    try:
        end = strpdatetime(request.json['end'])
    except KeyError:
        return Error('No end datetime specified.')
    except ValueError:
        return Error('Datetime must be in ISO format.')

    rentee = request.json.get('rentee')

    if not rentee:
        return Error('No rentee specified.')

    customer = request.json.get('customer')

    if not customer:
        return Error('No customer specified.')

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
