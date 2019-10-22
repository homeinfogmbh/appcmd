"""Renting."""

from datetime import datetime

from bookings import dom
from bookings import email
from bookings import AlreadyBooked
from bookings import EndBeforeStart
from bookings import DurationTooLong
from bookings import DurationTooShort
from bookings import Bookable
from bookings import Booking
from timelib import strpdatetime
from wsgilib import Error, OK, XML

from appcmd.functions import get_json, get_customer_and_address


__all__ = ['list_bookables', 'list_bookings', 'book']


def list_bookables():
    """Lists available bookables."""

    customer, _ = get_customer_and_address()
    xml = dom.bookables()

    for bookable in Bookable.select().where(Bookable.customer == customer):
        xml.bookable.append(bookable.to_dom())

    return XML(xml)


def list_bookings():
    """Lists stored bookings."""

    xml = dom.bookings()
    customer, _ = get_customer_and_address()

    for booking in Booking.select().join(Bookable).where(
            (Bookable.customer == customer)
            & (Booking.end >= datetime.now())).order_by(
                Booking.start):
        xml.booking.append(booking.to_dom())

    return XML(xml)


def book():     # pylint: disable=R0911
    """Books a bookable."""

    json = get_json()

    try:
        rentable = json['bookable']
    except KeyError:
        return Error('No bookable specified.')

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

    rentee = json.get('rentee') or None
    purpose = json.get('purpose') or None
    customer, _ = get_customer_and_address()

    try:
        bookable = Bookable.get(
            (Bookable.id == rentable) & (Bookable.customer == customer))
    except Bookable.DoesNotExist:
        return Error('No such bookable.', status=404)

    try:
        booking = bookable.book(start, end, rentee=rentee, purpose=purpose)
    except EndBeforeStart:
        return Error('Start date must be before end date.')
    except DurationTooLong:
        return Error('Rent duration is too long.')
    except DurationTooShort:
        return Error('Rent duration is too short.')
    except AlreadyBooked:
        return Error('Bookable has already been booked.', status=409)

    email(booking)
    return OK(f'{booking.id}')
