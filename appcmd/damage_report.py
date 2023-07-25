"""Damage report submission."""

from damage_report import email, DamageReport
from peeweeplus import FieldValueError, FieldNotNullable, InvalidKeys
from wsgilib import Error

from appcmd.functions import get_json, get_customer, get_address


__all__ = ["damage_report"]


ALLOWED_FIELDS = {"message", "name", "contact", "damage_type"}


def damage_report() -> tuple[str, int]:
    """Stores damage reports."""

    try:
        record = DamageReport.from_json(
            get_json(), get_customer(), get_address(), only=ALLOWED_FIELDS
        )
    except InvalidKeys as invalid_keys:
        raise Error(f"Invalid keys: {invalid_keys.invalid_keys}.") from None
    except FieldNotNullable as fnn:
        raise Error(f'Field "{fnn.field}" is not nullable.') from None
    except FieldValueError as fve:
        raise Error(f'Invalid value "{fve.field}": "{fve.value}".') from None

    record.save()
    email(record)
    return ("Damage report added.", 201)
