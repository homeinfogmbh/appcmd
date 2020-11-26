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

from appcmd.functions import get_json, get_customer


__all__ = ['list_bookables', 'list_bookings', 'book', 'cancel']


def get_booking(ident: int) -> Booking:
    """Returns the respective booking."""

    condition = Booking.id == ident
    condition &= Bookable.customer == get_customer()

    try:
        return Booking.select().join(Bookable).where(condition).get()
    except Booking.DoesNotExist:
        raise Error('No such booking.', status=404) from None


def get_bookable(json: dict) -> Bookable:
    """Returns the respective bookable."""

    condition = Bookable.customer == get_customer()

    try:
        condition &= Bookable.id == json['bookable']
    except KeyError:
        raise Error('No bookable specified.') from None

    try:
        return Bookable.get(condition)
    except Bookable.DoesNotExist:
        raise Error('No such bookable.', status=404) from None


def make_booking(bookable: Bookable, json: dict) -> Booking:
    """Adds a booking."""

    try:
        start = strpdatetime(json['start'])
    except KeyError:
        raise Error('No start datetime specified.') from None
    except ValueError:
        raise Error('Datetime must be in ISO format.') from None

    try:
        end = strpdatetime(json['end'])
    except KeyError:
        raise Error('No end datetime specified.') from None
    except ValueError:
        raise Error('Datetime must be in ISO format.') from None

    rentee = json.get('rentee') or None
    purpose = json.get('purpose') or None

    try:
        return bookable.book(start, end, rentee=rentee, purpose=purpose)
    except EndBeforeStart:
        raise Error('Start date must be before end date.') from None
    except DurationTooLong:
        raise Error('Rent duration is too long.') from None
    except DurationTooShort:
        raise Error('Rent duration is too short.') from None
    except AlreadyBooked:
        raise Error('Bookable has already been booked.', status=409) from None


def list_bookables() -> dom.bookables.typeDefinition():
    """Lists available bookables."""

    bookables = Bookable.select().where(Bookable.customer == get_customer())
    xml = dom.bookables()

    for bookable in bookables:
        xml.bookable.append(bookable.to_dom())

    return XML(xml)


def list_bookings() -> XML:
    """Lists stored bookings."""

    condition = Bookable.customer == get_customer()
    condition &= Booking.end >= datetime.now()
    bookings = Booking.select().join(Bookable).where(condition)
    xml = dom.bookings()

    for booking in bookings.order_by(Booking.start):
        xml.booking.append(booking.to_dom())

    return XML(xml)


def book() -> OK:     # pylint: disable=R0911
    """Books a bookable."""

    json = get_json()
    bookable = get_bookable(json)
    booking = make_booking(bookable, json)
    email(booking)
    return OK(f'{booking.id}')


def cancel(ident: int) -> OK:
    """Cancels a booking."""

    get_booking(ident).delete_instance()
    return OK('Booking cancelled.')
