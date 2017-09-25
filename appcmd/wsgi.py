"""WSGI handlers for appcmd."""

from json import loads
from urllib.parse import urlparse

from peewee import DoesNotExist
from requests import get

from aha import LocationNotFound, AhaDisposalClient
from homeinfo.crm import Customer
from homeinfo.terminals.orm import Terminal
from wsgilib import ResourceHandler, Response, OK, Error, JSON, \
    InternalServerError

from .mail import CouldNotSendMail, ContactFormMailer
from .orm import Command, Statistics, CleaningUser, CleaningDate, \
    TenantMessage, DamageReport, ProxyHost

__all__ = ['PrivateHandler', 'PublicHandler']


AHA_CLIENT = AhaDisposalClient()


def get_url(url):
    """Returns the content of the retrieved URL."""

    reply = get(url)

    try:
        content_type, charset = reply.headers['Content-Type'].split(';')
    except ValueError:
        content_type = reply.headers['Content-Type']
        charset = None
    else:
        _, charset = charset.split('=')

    return Response(
        msg=reply.content, status=reply.status_code,
        content_type=content_type, charset=charset, encoding=False)


class CommonBasicHandler(ResourceHandler):
    """Common handler base for private and public handler."""

    @property
    def cid(self):
        """Returns the customer ID."""
        try:
            return int(self.query['cid'])
        except KeyError:
            raise Error('No CID specified.') from None
        except (TypeError, ValueError):
            raise Error('CID must be an integer.') from None

    @property
    def tid(self):
        """Returns the presentation ID."""
        try:
            return int(self.query['tid'])
        except (KeyError, TypeError):
            return None
        except ValueError:
            raise Error('TID must be an integer.') from None

    @property
    def vid(self):
        """Returns the presentation ID."""
        try:
            return int(self.query['vid'])
        except KeyError:
            raise Error('No VID specified.') from None
        except TypeError:
            raise Error('VID must not be null.') from None
        except ValueError:
            raise Error('VID must be an integer.') from None

    @property
    def customer(self):
        """Returns the respective customer."""
        try:
            return Customer.get(Customer.id == self.cid)
        except DoesNotExist:
            raise Error('No such customer: {}.'.format(
                self.cid), status=404) from None

    @property
    def task(self):
        """Returns the respective task."""
        try:
            return self.query['task']
        except KeyError:
            raise Error('No task specified.') from None

    @property
    def document(self):
        """Returns the appropriate statistics document."""
        try:
            return self.query['document']
        except KeyError:
            raise Error('No document specified.') from None

    @property
    def pin(self):
        """Returns the cleaning PIN."""
        try:
            return self.query['pin']
        except KeyError:
            raise Error('No PIN provided.') from None

    @property
    def street(self):
        """Returns the street."""
        try:
            return self.query['street']
        except KeyError:
            raise Error('No street provided.') from None

    @property
    def house_number(self):
        """Returns the house_number."""
        try:
            return self.query['house_number']
        except KeyError:
            raise Error('No house_number provided.') from None

    @property
    def terminal(self):
        """Returns the respective customer."""
        try:
            return Terminal.by_ids(self.cid, self.tid)
        except DoesNotExist:
            raise Error('No such terminal: {}.{}.'.format(
                self.tid, self.cid), status=404) from None

    def list_commands(self):
        """Lists commands for the respective terminal."""
        tasks = []

        for command in Command.select().where(
                (Command.customer == self.customer) &
                (Command.vid == self.vid) &
                (Command.completed >> None)):
            tasks.append(command.task)

        return JSON(tasks)

    def list_cleanings(self):
        """Lists cleaning entries for the respective terminal."""
        try:
            address = self.terminal.location.address
        except AttributeError:
            raise Error('Terminal has no address.') from None
        else:
            return JSON(CleaningDate.by_address(address, limit=10))

    def complete_command(self):
        """Completes the provided command."""
        result = False

        for command in Command.select().where(
                (Command.customer == self.customer) &
                (Command.vid == self.vid) &
                (Command.task == self.task) &
                (Command.completed >> None)):
            command.complete()
            result = True

        return OK('1' if result else '0')

    def add_statistics(self):
        """Adds a new statistics entry."""
        Statistics.add(self.customer, self.vid, self.tid, self.document)
        return OK(status=201)

    def add_cleaning(self):
        """Adds a cleaning entry."""
        terminal = self.terminal

        try:
            user = CleaningUser.get(
                (CleaningUser.pin == self.pin) &
                (CleaningUser.customer == terminal.customer))
        except DoesNotExist:
            raise Error('Invalid PIN.', status=403) from None
        else:
            try:
                address = terminal.location.address
            except AttributeError:
                raise Error('Terminal has no address.') from None
            else:
                CleaningDate.add(user, address)
                return OK(status=201)

    def proxy(self):
        """Proxies URLs."""
        url = urlparse(self.data.text)

        if url.scheme in ('http', 'https'):
            if url.hostname != '':
                try:
                    ProxyHost.get(ProxyHost.hostname == url.hostname)
                except DoesNotExist:
                    raise Error(
                        'Host name is not whitelisted.',
                        status=403) from None
                else:
                    return get_url(url.geturl())
            else:
                raise Error('Host name must not be empty.') from None
        else:
            raise Error('Scheme must be HTTP or HTTPS.') from None

    def contact_mail(self):
        """Sends contact form emails."""
        mailer = ContactFormMailer(logger=self.logger)

        try:
            msg = mailer.send(self.data.json)
        except CouldNotSendMail:
            raise InternalServerError('Could not send email.') from None
        else:
            return OK(msg)

    def tenant2tenant(self, maxlen=2048):
        """Stores tenant info."""
        message = self.data.text

        if len(message) > maxlen:
            raise Error('Maximum text length exceeded.') from None
        else:
            TenantMessage.add(self.terminal, message)
            return OK(status=201)

    def damage_report(self):
        """Stores damage reports."""
        try:
            DamageReport.from_dict(self.terminal, self.data.json)
        except KeyError as key_error:
            raise Error('Missing mandatory property: {}.'.format(
                key_error.args[0])) from None
        else:
            return OK(status=201)

    def garbage_collection(self):
        """Returns information about the garbage collection."""
        try:
            pickups = [pickup.to_dict() for pickup in AHA_CLIENT.by_address(
                self.street, self.house_number)]
        except LocationNotFound:
            return Error('Location not found.', status=404)
        else:
            return JSON(pickups)


class PrivateHandler(CommonBasicHandler):
    """Handles data POSTed over VPN."""

    def post(self):
        """Handles POST requests."""
        if self.resource == 'contactform':
            return self.contact_mail()
        elif self.resource == 'tenant2tenant':
            return self.tenant2tenant()
        elif self.resource == 'damagereport':
            return self.damage_report()
        elif self.resource == 'statistics':
            return self.add_statistics()
        else:
            raise Error('Invalid operation.') from None


class PublicHandler(CommonBasicHandler):
    """Handles data POSTed over the internet."""

    def get(self):
        """Handles GET requests."""
        if self.resource == 'command':
            return self.list_commands()
        elif self.resource == 'cleaning':
            return self.list_cleanings()
        elif self.resource == 'garbage_collection':
            return self.garbage_collection()
        else:
            raise Error('Invalid operation.') from None

    def post(self):
        """Handles POST requests."""
        if self.resource == 'command':
            return self.complete_command()
        elif self.resource == 'statistics':
            return self.add_statistics()
        elif self.resource == 'cleaning':
            return self.add_cleaning()
        elif self.resource == 'proxy':
            return self.proxy()
        else:
            raise Error('Invalid operation.') from None
