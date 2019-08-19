"""Renting."""

from flask import request

from rentallib import AlreadyRented
from rentallib import EndBeforeStart
from rentallib import DurationTooLong
from rentallib import DurationTooShort
from rentallib import Rentable
from timelib import strpdatetime
from wsgilib import Error, OK


def rent():
    """Rents a rentable."""

    try:
        rentable = request.json['rentable']
    except KeyError:
        raise Error('No rentable specified.')

    try:
        start = strpdatetime(request.json['start'])
    except KeyError:
        raise Error('No start datetime specified.')
    except ValueError:
        raise Error('Datetime must be in ISO format.')

    try:
        end = strpdatetime(request.json['end'])
    except KeyError:
        raise Error('No end datetime specified.')
    except ValueError:
        raise Error('Datetime must be in ISO format.')

    rentee = request.json.get('rentee')

    if not rentee:
        raise Error('No rentee specified.')

    customer = request.json.get('customer')

    if not customer:
        raise Error('No customer specified.')

    try:
        rentable = Rentable.get(
            (Rentable.id == rentable) & (Rentable.customer == customer))
    except Rentable.DoesNotExist:
        raise Error('No such rentable.', status=404)

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
