"""Damage report submission."""

from appcmd.functions import get_customer_and_address

from digsigdb import DamageReport
from peeweeplus import FieldValueError, FieldNotNullable, InvalidKeys
from wsgilib import PostData, Error

__all__ = ['damage_report']


DATA = PostData()


def damage_report():
    """Stores damage reports."""

    customer, address = get_customer_and_address()

    try:
        record = DamageReport.from_dict(customer, address, DATA.json)
    except InvalidKeys as invalid_keys:
        raise Error('Invalid keys: {}.'.format(invalid_keys.invalid_keys))
    except FieldNotNullable as field_not_nullable:
        raise Error('Field "{}" is not nullable.'.format(
            field_not_nullable.field))
    except FieldValueError as field_value_error:
        raise Error('Invalid value for field "{}": "{}".'.format(
            field_value_error.field, field_value_error.value))

    record.save()
    return ('Damage report added.', 201)
