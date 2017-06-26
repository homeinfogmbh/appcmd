"""WSGI handlers for appcmd"""

from json import loads
from peewee import DoesNotExist

from homeinfo.applicationdb import Command, Statistics, CleaningUser, \
    CleaningDate, TenantMessage, DamageReport
from homeinfo.crm import Customer
from homeinfo.terminals.orm import Terminal
from wsgilib import ResourceHandler, OK, JSON, InternalServerError

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
            raise self.logerr('No CID specified.') from None
        except TypeError:
            raise self.logerr('CID must not be null.') from None
        except ValueError:
            raise self.logerr('CID must be an integer.') from None

    @property
    def tid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['tid'])
        except KeyError:
            raise self.logerr('No TID specified.') from None
        except TypeError:
            raise self.logerr('TID must not be null.') from None
        except ValueError:
            raise self.logerr('TID must be an integer.') from None

    @property
    def terminal(self):
        """Returns the respective customer"""
        try:
            return Terminal.by_ids(self.cid, self.tid)
        except DoesNotExist:
            raise self.logerr('No such terminal: {}.{}.'.format(
                self.tid, self.cid)) from None


class PrivateHandler(CommonBasicHandler):
    """Handles posted data for legacy mode"""

    def post(self):
        """Handles POST requests"""
        if self.resource == 'contactform':
            return self._contact_mail()
        elif self.resource == 'tenant2tenant':
            return self._tenant2tenant()
        elif self.resource == 'damagereport':
            return self._damage_report()
        else:
            raise self.logerr('Invalid operation.') from None

    def _contact_mail(self):
        """Sends contact form emails"""
        try:
            dictionary = loads(self.data.decode())
        except AttributeError:
            raise self.logerr('No data provided.') from None
        except ValueError:
            raise self.logerr('Data is not UTF-8 encoded JSON.') from None
        else:
            mailer = ContactFormMailer(logger=self.logger)

            try:
                msg = mailer.send(dictionary)
            except Exception:
                raise InternalServerError('Could not send email.') from None
            else:
                return OK(msg)

    def _tenant2tenant(self, maxlen=2048):
        """Stores tenant info"""
        try:
            message = self.data.decode()
        except AttributeError:
            raise self.logerr('No message provided.') from None
        except ValueError:
            raise self.logerr('Data is not UTF-8 text.') from None
        else:
            if len(message) > maxlen:
                raise self.logerr('Maximum text length exceeded.') from None
            else:
                TenantMessage.add(self.terminal, message)
                return OK(status=201)

    def _damage_report(self):
        """Stores damage reports"""
        try:
            dictionary = loads(self.data.decode())
        except AttributeError:
            raise self.logerr('No message provided.') from None
        except ValueError:
            raise self.logerr('Data is not UTF-8 JSON.') from None
        else:
            try:
                DamageReport.from_dict(self.terminal, dictionary)
            except KeyError as ke:
                raise self.logerr('Missing mandatory property: {}.'.format(
                    ke.args[0])) from None
            else:
                return OK(status=201)


class PublicHandler(CommonBasicHandler):
    """Public services handler"""

    @property
    def vid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['vid'])
        except KeyError:
            raise self.logerr('No VID specified.') from None
        except TypeError:
            raise self.logerr('VID must not be null.') from None
        except ValueError:
            raise self.logerr('VID must be an integer.') from None

    @property
    def customer(self):
        """Returns the respective customer"""
        try:
            return Customer.find(self.cid)
        except DoesNotExist:
            raise self.logerr(
                'No such customer: {}.'.format(self.cid)) from None

    @property
    def task(self):
        """Returns the respective task"""
        try:
            task = self.query['task']
        except KeyError:
            raise self.logerr('No task specified.') from None
        else:
            if task is None:
                raise self.logerr('Task must not be null.') from None
            else:
                return task

    def get(self):
        """Handles GET requests"""
        if self.resource == 'command':
            return self._list_commands()
        elif self.resource == 'cleaning':
            return self._list_cleanings()
        else:
            raise self.logerr('Invalid operation.') from None

    def post(self):
        """Handles POST requests"""
        if self.resource == 'command':
            return self._complete_command()
        elif self.resource == 'statistics':
            return self._add_statistics()
        elif self.resource == 'cleaning':
            return self._add_cleaning()
        else:
            raise self.logerr('Invalid operation.') from None

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
        try:
            address = self.terminal.location.address
        except AttributeError:
            raise self.logerr('Terminal has no address.') from None
        else:
            return JSON(CleaningDate.of(address, limit=10))

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
            raise self.logerr('TID must be an integer') from None
        except TypeError:
            tid = None

        try:
            document = self.query['document']
        except KeyError:
            raise self.logerr('Document must not be null.') from None
        else:
            if document is None:
                raise self.logerr('Document must not be null.') from None

        try:
            Statistics.add(customer, vid, tid, document)
        except Exception as e:
            raise InternalServerError(str(e)) from None
        else:
            return OK(status=201)

    def _add_cleaning(self):
        """Adds a cleaning entry"""
        try:
            pin = int(self.query['pin'])
        except KeyError:
            raise self.logerr('No PIN provided.') from None
        except TypeError:
            raise self.logerr('PIN must not be null.') from None
        except ValueError:
            raise self.logerr('PIN must be an integer.') from None
        else:
            terminal = self.terminal

            try:
                user = CleaningUser.get(
                    (CleaningUser.pin == pin) &
                    (CleaningUser.customer == terminal.customer))
            except DoesNotExist:
                raise self.logerr('Invalid PIN.', status=403) from None
            else:
                try:
                    address = terminal.location.address
                except AttributeError:
                    raise self.logerr('Terminal has no address.') from None
                else:
                    CleaningDate.add(user, address)
                    return OK(status=201)
