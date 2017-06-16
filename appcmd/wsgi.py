#! /usr/bin/env python3
#
# HOMEINFO mailer backend for Digital
# Signage Application contact forms
#
# 01.11.2016: Richard Neumann <r.neumann@homeinfo.de>
#
################################################################

from peewee import DoesNotExist

from homeinfo.applicationdb import TenantMessage, Command, Cleaning
from homeinfo.crm import Customer
from homeinfo.terminals.orm import Terminal
from wsgilib import ResourceHandler, CachedJSONHandler, OK, JSON

from .mail import ContactFormMailer

__all__ = ['PrivateHandler', 'PublicHandler']


class CachedTerminalHandler(CachedJSONHandler):
    """Caches also terminals and customers"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._customer = None
        self._terminal = None

    @property
    def customer(self):
        """Returns the customer"""
        if self._customer is None:
            try:
                cid = self.dictionary['cid']
            except KeyError:
                self.lograise('No CID provided.')
            else:
                try:
                    self._customer = Customer.find(cid)
                except DoesNotExist:
                    self.lograise('No such customer.')

        return self._customer

    @property
    def terminal(self):
        """Returns the terminal"""
        if self._terminal is None:
            try:
                tid = self.dictionary['tid']
            except KeyError:
                self.lograise('No TID provided.')
            else:
                try:
                    return int(tid)
                except TypeError:
                    self.lograise('TID must not be null.')
                except ValueError:
                    self.lograise('TID is not an integer.')
                else:
                    try:
                        self._terminal = Terminal.get(
                            (Terminal.customer == self.customer) &
                            (Terminal.tid == tid))
                    except DoesNotExist:
                        self.lograise('No such terminal.')

        return self._terminal


class PrivateHandler(CachedTerminalHandler):
    """Handles posted data for legacy mode"""

    def post(self):
        """Handles POST requests"""
        if self.resource == 'contactform':
            return self._contact_mail()
        elif self.resource == 'tenant2tenant':
            return self._tenant2tenant()
        else:
            self.lograise('Invalid operation.')

    def _contact_mail(self):
        """Sends contact form emails"""
        mailer = ContactFormMailer(logger=self.logger)
        return mailer.send(self.dictionary)

    def _tenant2tenant(self, maxlen=2048):
        """Stores tenant info"""
        try:
            message = self.dictionary['message']
        except KeyError:
            self.lograise('No message provided.')
        else:
            if message is None:
                self.lograise('Message must not be None.')
            elif len(message) > maxlen:
                self.lograise('Maximum text length exceeded.')
            else:
                TenantMessage.add(self.terminal, message)
                return OK()


class PublicHandler(ResourceHandler):
    """Public services handler"""

    @property
    def cid(self):
        """Returns the customer ID"""
        try:
            return int(self.query['cid'])
        except KeyError:
            self.lograise('No CID specified.')
        except TypeError:
            self.lograise('CID must not be null.')
        except ValueError:
            self.lograise('CID must be an integer.')

    @property
    def vid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['vid'])
        except KeyError:
            self.lograise('No VID specified.')
        except TypeError:
            self.lograise('VID must not be null.')
        except ValueError:
            self.lograise('VID must be an integer.')

    @property
    def tid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['tid'])
        except KeyError:
            self.lograise('No TID specified.')
        except TypeError:
            self.lograise('TID must not be null.')
        except ValueError:
            self.lograise('TID must be an integer.')

    @property
    def customer(self):
        """Returns the respective customer"""
        try:
            return Customer.find(self.cid)
        except DoesNotExist:
            self.lograise('No such customer: {}.'.format(self.cid))

    @property
    def terminal(self):
        """Returns the respective customer"""
        try:
            return Terminal.by_ids(self.cid, self.tid)
        except DoesNotExist:
            self.lograise('No such terminal: {}.{}.'.format(
                self.tid, self.cid))

    @property
    def task(self):
        """Returns the respective task"""
        try:
            task = self.query['task']
        except KeyError:
            self.lograise('No task specified.')
        else:
            if task is None:
                self.lograise('Task must not be null.')
            else:
                return task

    def get(self):
        """Handles GET requests"""
        if self.resource == 'command':
            return self._list_commands()
        elif self.resource == 'controller':
            return self._get_controller_ip()
        elif self.resource == 'cleaning':
            return self._list_cleanings()
        else:
            self.lograise('Invalid operation.')

    def post(self):
        """Handles POST requests"""
        if self.resource == 'command':
            return self._complete_command()
        elif self.resource == 'statistics':
            return self._add_statistics()
        elif self.resource == 'controller':
            return self._update_controller()
        elif self.resource == 'cleaning':
            return self._add_cleaning()
        else:
            self.lograise('Invalid operation.')

    def _list_commands(self):
        """Lists commands for the respective terminal"""
        customer = self.customer
        vid = self.vid
        tasks = []

        for command in Command.select().where(
                (Command.customer == customer) &
                (Command.vid == vid) &
                (Command.completed >> None)):
            tasks.append(command.task)

        return JSON(tasks)

    def _list_cleanings(self):
        """Lists cleaning entries for the respective terminal"""
        cleanings = []

        for cleaning in Cleaning.select().where(
                Cleaning.terminal == self.terminal):
            cleanings.append(cleaning.to_dict())

        return JSON(cleanings)

    def _complete_command(self):
        """Completes the provided command"""
        customer = self.customer
        vid = self.vid
        task = self.task
        result = False

        for command in Command.select().where(
                (Command.customer == customer) &
                (Command.vid == vid) &
                (Command.task == task) &
                (Command.completed >> None)):
            command.complete()
            result = True

        return OK('1' if result else '0')
