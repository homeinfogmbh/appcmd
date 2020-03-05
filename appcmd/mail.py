"""Contact form E-Mail API."""

from contextlib import suppress
from datetime import datetime
from traceback import format_exc

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

    def __init__(self, stacktrace):
        """Sets the stacktrace."""
        super().__init__(stacktrace)
        self.stacktrace = stacktrace


def bool2lang(boolean, true='ja', false='nein'):
    """Converts a boolean value into natural language words."""

    return true if boolean else false


def get_text(dictionary, template=EMAIL_TEMP):
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


def send_contact_mail():
    """Sends contact form emails."""

    email = ContactFormEmail.from_json(get_json())

    try:
        return MAILER.send_email(email)
    except CouldNotSendMail:
        raise Error('Could not send email.', status=500)


class ContactFormEmail(EMail):
    """An email for the contact form."""

    @classmethod
    def from_json(cls, dictionary):
        """Creates a new email from the provided dictionary."""
        email = cls(
            CONFIG_SECTION['subject'], CONFIG_SECTION['sender'],
            dictionary['empfaenger'], plain=get_text(dictionary))

        with suppress(KeyError):
            email['Reply-To'] = dictionary['email']

        return email


class ContactFormMailer(Mailer):
    """A contact form mailer."""

    def __init__(self, logger=None):
        """Initializes the mailer with the appropriate configuration."""
        super().__init__(
            CONFIG_SECTION['host'], CONFIG_SECTION['port'],
            CONFIG_SECTION['user'], CONFIG_SECTION['passwd'], logger=logger)

    def send_email(self, email):
        """Sends contact form emails from JSON-like dictionary."""
        try:
            self.send([email], background=False)
        except Exception:
            stacktrace = format_exc()
            self.logger.error('Error while sending email.')
            self.logger.debug(stacktrace)
            raise CouldNotSendMail(stacktrace)

        return 'Sent email to: "{}".'.format(email.recipient)


MAILER = ContactFormMailer()
