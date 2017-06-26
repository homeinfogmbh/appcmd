"""Contact form and E-Mail API"""

from datetime import datetime
from traceback import format_exc

from emaillib import Mailer, EMail

from .config import config

SENDER = 'automailer@homeinfo.de'
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


def bool2lang(b, true='ja', false='nein'):
    """Converts a boolean value into natural language words"""

    return true if b else false


class ContactFormMailer(Mailer):
    """A contact form mailer"""

    def __init__(self, logger=None):
        """Initializes the mailer with the appropriate configuration"""
        super().__init__(
            config['mail']['host'], config['mail']['port'],
            config['mail']['user'], config['mail']['passwd'], logger=logger)

    def send(self, dictionary):
        """Sends contact form emails from JSON-like dictionary"""
        subject = 'Kontaktanfrage vom Immobiliendisplay'
        text = EMAIL_TEMP.format(
            datum=datetime.strftime(datetime.now(), '%d.%m.%Y %H:%M:%S'),
            objektnr=dictionary.get('objektnummer', 'unbekannt'),
            name=dictionary.get('name'),
            telefon=dictionary.get('telefon', 'nicht angegeben'),
            email=dictionary.get('email', 'nicht angegeben'),
            freitext=dictionary.get('freitext'),
            rueckruf=bool2lang(dictionary.get('rueckruf')),
            besichtigungstermin=bool2lang(
                dictionary.get('besichtigungstermin')),
            objektbeschreibung=bool2lang(
                dictionary.get('objektbeschreibung')))
        recipient = dictionary.get('empfaenger')
        email = EMail(subject, SENDER, recipient, plain=text)
        reply_to = dictionary.get('email')

        if reply_to:
            email['Reply-To'] = reply_to
            self.logger.debug('Reply to: {}'.format(reply_to))

        try:
            super().send([email])
        except Exception:
            self.logger.error('Error while sending email.')
            print(format_exc(), flush=True)
            raise
        else:
            return 'Sent email to: {}'.format(recipient)
