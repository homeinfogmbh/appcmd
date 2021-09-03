"""Contact form E-Mail API."""

from __future__ import annotations
from contextlib import suppress
from datetime import datetime
from typing import Union

from emaillib import Mailer, EMail
from wsgilib import Error

from appcmd.config import CONFIG
from appcmd.functions import get_json


__all__ = ['send_contact_mail']


CONFIG_SECTION = CONFIG['EMail']
EMAIL_TEMP = '''Kontaktformular vom {datum}:
-----------------------------------------------

Objekt:                        {objektnr}
Name:                          {name}
Telefon:                       {telefon}
Email:                         {email}
Nachricht:                     {freitext}
Rückruf erbeten:               {rueckruf}
Besichtigungstermin erwünscht: {besichtigungstermin}
Objektbeschreibung:            {objektbeschreibung}
'''


class CouldNotSendMail(Exception):
    """Indicates that emails could not be sent."""

    def __init__(self, stacktrace: str):
        """Sets the stacktrace."""
        super().__init__(stacktrace)
        self.stacktrace = stacktrace


def bool2lang(boolean: bool, *, true: str = 'ja', false: str = 'nein') -> str:
    """Converts a boolean value into natural language words."""

    return true if boolean else false


def get_text(dictionary: dict, template: str = EMAIL_TEMP) -> str:
    """Returns the formatted text template."""

    return template.format(
        datum=datetime.strftime(datetime.now(), '%d.%m.%Y %H:%M:%S'),
        objektnr=dictionary.get('objektnummer', 'unbekannt'),
        name=dictionary.get('name'),
        telefon=dictionary.get('telefon', 'nicht angegeben'),
        email=dictionary.get('email', 'nicht angegeben'),
        freitext=dictionary.get('freitext'),
        rueckruf=bool2lang(dictionary.get('rueckruf')),
        besichtigungstermin=bool2lang(dictionary.get('besichtigungstermin')),
        objektbeschreibung=bool2lang(dictionary.get('objektbeschreibung'))
    )


def send_contact_mail() -> Union[str, Error]:
    """Sends contact form emails."""

    email = ContactFormEmail.from_json(get_json())

    if MAILER.send(email):
        return f'Sent email to: {email.recipient}'

    return Error('Could not send email.', status=500)


class ContactFormEmail(EMail):
    """An email for the contact form."""

    @classmethod
    def from_json(cls, dictionary: dict) -> ContactFormEmail:
        """Creates a new email from the provided dictionary."""
        email = cls(
            CONFIG_SECTION['subject'], CONFIG_SECTION['sender'],
            dictionary['empfaenger'], plain=get_text(dictionary))

        with suppress(KeyError):
            email['Reply-To'] = dictionary['email']

        return email


MAILER = Mailer(
    CONFIG_SECTION['host'], CONFIG_SECTION['port'], CONFIG_SECTION['user'],
    CONFIG_SECTION['passwd']
)
