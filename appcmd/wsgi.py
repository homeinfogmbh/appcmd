#! /usr/bin/env python3
#
# HOMEINFO mailer backend for Digital
# Signage Application contact forms
#
# 01.11.2016: Richard Neumann <r.neumann@homeinfo.de>
#
################################################################

from json import loads

from wsgilib import Error, ResourceHandler

from .mail import ContactFormMailer

__all__ = ['AppcmdHandler']


class AppcmdHandler(ResourceHandler):
    """Handles posted data for legacy mode"""

    @property
    def json(self):
        """Returns the appropriate JSON dictionary"""
        try:
            text = self.data.decode()
        except AttributeError:
            raise Error('No data provided.') from None
        except UnicodeDecodeError:
            error = 'Non-unicode data received'
            self.logger.error('{}:\n{}'.format(error, self.data))
            raise Error('{}.'.format(error)) from None
        else:
            try:
                return loads(text)
            except ValueError:
                error = 'Non-JSON text received'
                self.logger.error('{}:\n{}'.format(error, text))
                raise Error('{}.'.format(error)) from None

    def post(self):
        """Handles POST requests"""
        dictionary = self.json

        if self.resource is None:
            try:
                command = dictionary['command']
            except KeyError:
                error = 'No command provided.'
                self.logger.error(error)
                raise Error(error) from None
            else:
                if command == 2:
                    return self._mail(dictionary)
                elif command == 3:
                    return self._rec_cleaning(dictionary)
                elif command == 5:
                    return self._rec_statistics(dictionary)
                else:
                    error = 'Unknown command: {}.'.format(command)
                    self.logger.error(error)
                    raise Error(error) from None
        elif self.resource == 'contactform':
            return self._contact_mail(dictionary)
        elif self.resource == 'cleaning_log':
            return self._rec_cleaning(dictionary)
        elif self.resource == 'statistics':
            return self._rec_statistics(dictionary)
        else:
            error = 'Invalid operation: {}'.format(self.resource)
            self.logger.error('{}.'.format(error))
            raise Error('{}.'.format(error)) from None

    def _contact_mail(self, dictionary):
        """Sends contact form emails"""
        mailer = ContactFormMailer(logger=self.logger)
        return mailer.send(dictionary)
