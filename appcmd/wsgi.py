"""WSGI handlers for appcmd"""

from json import loads
from peewee import DoesNotExist

from homeinfo.applicationdb import Command, Statistic, CleaningUser, Cleaning,\
    TenantMessage
from homeinfo.crm import Customer
from homeinfo.terminals.orm import Terminal
from wsgilib import ResourceHandler, OK, JSON

from .mail import ContactFormMailer

__all__ = ['PrivateHandler', 'PublicHandler']


class CommonBasicHandler(ResourceHandler):
    """Caches also terminals and customers"""

    @property
    def cid(self):
        """Returns the customer ID"""
        try:
            return int(self.query['cid'])
        except KeyError:
            return self.logerr('No CID specified.')
        except TypeError:
            return self.logerr('CID must not be null.')
        except ValueError:
            return self.logerr('CID must be an integer.')

    @property
    def tid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['tid'])
        except KeyError:
            return self.logerr('No TID specified.')
        except TypeError:
            return self.logerr('TID must not be null.')
        except ValueError:
            return self.logerr('TID must be an integer.')

    @property
    def terminal(self):
        """Returns the respective customer"""
        try:
            return Terminal.by_ids(self.cid, self.tid)
        except DoesNotExist:
            return self.logerr('No such terminal: {}.{}.'.format(
                self.tid, self.cid))


class PrivateHandler(CommonBasicHandler):
    """Handles posted data for legacy mode"""

    def post(self):
        """Handles POST requests"""
        if self.resource == 'contactform':
            return self._contact_mail()
        elif self.resource == 'tenant2tenant':
            return self._tenant2tenant()
        else:
            return self.logerr('Invalid operation.')

    def _contact_mail(self):
        """Sends contact form emails"""
        try:
            dictionary = loads(self.data.decode())
        except AttributeError:
            return self.logerr('No data provided.')
        except ValueError:
            return self.logerr('Data is not UTF-8 encoded JSON.')
        else:
            mailer = ContactFormMailer(logger=self.logger)
            return mailer.send(dictionary)

    def _tenant2tenant(self, maxlen=2048):
        """Stores tenant info"""
        try:
            message = self.data.decode()
        except AttributeError:
            return self.logerr('No message provided.')
        except ValueError:
            return self.logerr('Data is not UTF-8 text.')
        else:
            if len(message) > maxlen:
                return self.logerr('Maximum text length exceeded.')
            else:
                TenantMessage.add(self.terminal, message)
                return OK()


class PublicHandler(CommonBasicHandler):
    """Public services handler"""

    @property
    def vid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['vid'])
        except KeyError:
            return self.logerr('No VID specified.')
        except TypeError:
            return self.logerr('VID must not be null.')
        except ValueError:
            return self.logerr('VID must be an integer.')

    @property
    def customer(self):
        """Returns the respective customer"""
        try:
            return Customer.find(self.cid)
        except DoesNotExist:
            return self.logerr('No such customer: {}.'.format(self.cid))

    @property
    def task(self):
        """Returns the respective task"""
        try:
            task = self.query['task']
        except KeyError:
            return self.logerr('No task specified.')
        else:
            if task is None:
                return self.logerr('Task must not be null.')
            else:
                return task

    def get(self):
        """Handles GET requests"""
        if self.resource == 'command':
            return self._list_commands()
        elif self.resource == 'cleaning':
            return self._list_cleanings()
        else:
            return self.logerr('Invalid operation.')

    def post(self):
        """Handles POST requests"""
        if self.resource == 'command':
            return self._complete_command()
        elif self.resource == 'statistics':
            return self._add_statistics()
        elif self.resource == 'cleaning':
            return self._add_cleaning()
        else:
            return self.logerr('Invalid operation.')

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

    def _add_statistics(self):
        """Adds a new statistics entry"""
        customer = self.customer
        vid = self.vid

        try:
            tid = int(self.query['tid'])
        except KeyError:
            tid = None
        except ValueError:
            return self.logerr('TID must be an integer')
        except TypeError:
            tid = None

        try:
            document = self.query['document']
        except KeyError:
            return self.logerr('Document must not be null.')
        else:
            if document is None:
                return self.logerr('Document must not be null.')

        Statistic.add(customer, vid, tid, document)
        return OK()

    def _add_cleaning(self):
        """Adds a cleaning entry"""
        try:
            name = self.query['user']
        except KeyError:
            return self.logerr('No user name specified.')
        else:
            if name is None:
                return self.logerr('User name must not be null.')

        try:
            pin = int(self.query['pin'])
        except KeyError:
            return self.logerr('No PIN provided.')
        except TypeError:
            return self.logerr('PIN must not be null.')
        except ValueError:
            return self.logerr('PIN must be an integer.')

        try:
            user = CleaningUser.get(
                (CleaningUser.name == name)
                (CleaningUser.customer == self.customer))
        except DoesNotExist:
            return self.logerr('No such user.')
        else:
            if user.pin == pin:
                Cleaning.add(user, self.terminal.location.address)
                return OK()
            else:
                return self.logerr('Invalid PIN.')
