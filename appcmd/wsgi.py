#! /usr/bin/env python3
#
# HOMEINFO mailer backend for Digital
# Signage Application contact forms
#
# 01.11.2016: Richard Neumann <r.neumann@homeinfo.de>
#
################################################################

from json import loads
from datetime import datetime
from traceback import format_exc

from homeinfo.lib.wsgi import Error, OK, WsgiApp, RequestHandler
from homeinfo.lib.mail import Mailer, EMail


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


class MailingHandler(RequestHandler):
    """Handles posted mail"""

    def __init__(self, *args, logger=None, **kwargs):
        super().__init__(*args, logger=logger, **kwargs)
        self.mailer = Mailer(
            'mail.homeinfo.de', 25, 'web0p6',
            '307U~x3]m7E8', logger=logger)

    def post(self):
        """Handles POST requests"""
        try:
            text = self.data.decode()
        except AttributeError:
            raise Error('No data provided') from None
        except UnicodeDecodeError:
            self.logger.error('Non-unicode data received:\n{}'.format(
                self.data))
            raise Error('Non-unicode string received') from None
        else:
            try:
                dictionary = loads(text)
            except ValueError:
                self.logger.error('Non-JSON text received:\n{}'.format(text))
                raise Error('Non-JSON data received') from None
            else:
                try:
                    command = dictionary['command']
                except KeyError:
                    raise Error('No command provided') from None
                else:
                    if command == 2:
                        return self._mail(dictionary)
                    elif command == 3:
                        return self._rec_clean(dictionary)
                    elif command == 5:
                        return self._rec_stat(dictionary)
                    else:
                        raise Error('Unknown command: {}'.format(
                            command)) from None

    def _mail(self, dictionary):
        """Sends contact form emails"""
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
        self.logger.debug('Rendered text:\n{}'.format(text))
        recipient = dictionary.get('empfaenger')
        self.logger.debug('Recipient is: {}'.format(recipient))
        email = EMail(subject, SENDER, recipient, plain=text)
        reply_to = dictionary.get('email')

        if reply_to:
            email['Reply-To'] = reply_to
            self.logger.debug('Reply to: {}'.format(reply_to))

        try:
            self.mailer.send([email])
        except Exception:
            msg = 'Error while sending email'
            self.logger.error(msg)
            print(format_exc(), flush=True)
            raise Error(msg)
        else:
            msg = 'Sent email to: {}'.format(recipient)
            return OK(msg)


application = WsgiApp(MailingHandler, debug=True)

