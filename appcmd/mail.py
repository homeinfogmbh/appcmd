"""Contact form E-Mail API."""

from __future__ import annotations
from datetime import datetime
from typing import Union

from emaillib import Mailer, EMail
from wsgilib import Error

from appcmd.config import get_config
from appcmd.functions import get_json


__all__ = ["send_contact_mail"]


EMAIL_TEMP = """Kontaktformular vom {datum}:
-----------------------------------------------

Objekt:                        {objektnr}
Name:                          {name}
Telefon:                       {telefon}
Email:                         {email}
Nachricht:                     {freitext}
Rückruf erbeten:               {rueckruf}
Besichtigungstermin erwünscht: {besichtigungstermin}
Objektbeschreibung:            {objektbeschreibung}
"""


def get_mailer() -> Mailer:
    """Returns the mailer."""

    return Mailer(
        (config := get_config()).get("EMail", "host"),
        config.get("EMail", "port"),
        config.get("EMail", "user"),
        config.get("EMail", "passwd"),
    )


class CouldNotSendMail(Exception):
    """Indicates that emails could not be sent."""

    def __init__(self, stacktrace: str):
        """Sets the stacktrace."""
        super().__init__(stacktrace)
        self.stacktrace = stacktrace


def bool2lang(boolean: bool, *, true: str = "ja", false: str = "nein") -> str:
    """Converts a boolean value into natural language words."""

    return true if boolean else false


def get_text(params: dict, template: str = EMAIL_TEMP) -> str:
    """Returns the formatted text template."""

    return template.format(
        datum=datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S"),
        objektnr=params.get("objektnummer", "unbekannt"),
        name=params.get("name"),
        telefon=params.get("telefon", "nicht angegeben"),
        email=params.get("email", "nicht angegeben"),
        freitext=params.get("freitext"),
        rueckruf=bool2lang(params.get("rueckruf")),
        besichtigungstermin=bool2lang(params.get("besichtigungstermin")),
        objektbeschreibung=bool2lang(params.get("objektbeschreibung")),
    )


def send_contact_mail() -> Union[str, Error]:
    """Sends contact form emails."""

    email = ContactFormEmail.from_json(get_json())

    if get_mailer().send([email]):
        return f"Sent email to: {email.recipient}"

    return Error("Could not send email.", status=500)


class ContactFormEmail(EMail):
    """An email for the contact form."""

    @classmethod
    def from_json(cls, params: dict) -> ContactFormEmail:
        """Creates a new email from the provided dictionary."""
        return cls(
            (config := get_config()).get("EMail", "subject"),
            config.get("EMail", "sender"),
            params["empfaenger"],
            reply_to=params.get("email"),
            plain=get_text(params),
        )
