"""Damage report submission."""

from damage_report import email, DamageReport
from peeweeplus import FieldValueError, FieldNotNullable, InvalidKeys
from wsgilib import Error

from appcmd.functions import get_json, get_customer, get_address


__all__ = ['damage_report']


ALLOWED_FIELDS = {'message', 'name', 'contact', 'damage_type'}


def damage_report():
    """Stores damage reports."""

    try:
        record = DamageReport.from_json(
            get_json(), get_customer(), get_address(), only=ALLOWED_FIELDS)
    except InvalidKeys as invalid_keys:
        raise Error(f'Invalid keys: {invalid_keys.invalid_keys}.')
    except FieldNotNullable as field_not_nullable:
        raise Error(f'Field "{field_not_nullable.field}" is not nullable.')
    except FieldValueError as field_value_error:
        raise Error(
            f'Invalid value for field "{field_value_error.field}": '
            f'"{field_value_error.value}".')

    record.save()
    email(record)
    return ('Damage report added.', 201)
