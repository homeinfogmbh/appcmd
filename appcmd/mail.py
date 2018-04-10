"""Contact form E-Mail API."""

from contextlib import suppress
from datetime import datetime
from traceback import format_exc

from emaillib import Mailer, EMail

from appcmd.config import CONFIG

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
    """Converts a boolean value into natural language words"""

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
        objektbeschreibung=bool2lang(dictionary.get('objektbeschreibung')))


class ContactFormEmail(EMail):
    """An email for the contact form."""

    @classmethod
    def from_dict(cls, dictionary):
        """Creates a new email from the provided dictionary."""
        email = cls(
            CONFIG['mail']['subject'], CONFIG['mail']['sender'],
            dictionary['empfaenger'], plain=get_text(dictionary))

        with suppress(KeyError):
            email['Reply-To'] = dictionary['email']

        return email


class ContactFormMailer(Mailer):
    """A contact form mailer."""

    def __init__(self, logger=None):
        """Initializes the mailer with the appropriate configuration."""
        super().__init__(
            CONFIG['mail']['host'], CONFIG['mail']['port'],
            CONFIG['mail']['user'], CONFIG['mail']['passwd'], logger=logger)

    def send_email(self, email):
        """Sends contact form emails from JSON-like dictionary."""
        try:
            self.send([email])
        except Exception:
            stacktrace = format_exc()
            self.logger.error('Error while sending email.')
            self.logger.debug(stacktrace)
            raise CouldNotSendMail(stacktrace)

        return 'Sent email to: "{}".'.format(email.recipient)
