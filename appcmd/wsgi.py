"""WSGI handlers for appcmd"""

from json import loads
from peewee import DoesNotExist
from requests import get
from urllib.parse import urlparse

from homeinfo.applicationdb import Command, Statistics, CleaningUser, \
    CleaningDate, TenantMessage, DamageReport, ProxyHost
from homeinfo.crm import Customer
from homeinfo.terminals.orm import Terminal
from wsgilib import ResourceHandler, Response, OK, JSON, InternalServerError

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
        except (TypeError, ValueError):
            raise self.logerr('CID must be an integer.') from None

    @property
    def tid(self):
        """Returns the presentation ID"""
        try:
            return int(self.query['tid'])
        except (KeyError, TypeError):
            return None
        except ValueError:
            raise self.logerr('TID must be an integer.') from None

    @property
    def terminal(self):
        """Returns the respective customer"""
        tid = self.tid

        if tid is None:
            raise self.logerr('No TID specified.') from None
        else:
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
            return self.contact_mail()
        elif self.resource == 'tenant2tenant':
            return self.tenant2tenant()
        elif self.resource == 'damagereport':
            return self.damage_report()
        else:
            raise self.logerr('Invalid operation.') from None

    def contact_mail(self):
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

    def tenant2tenant(self, maxlen=2048):
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

    def damage_report(self):
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
            raise self.logerr('No such customer: {}.'.format(
                self.cid)) from None

    @property
    def task(self):
        """Returns the respective task"""
        try:
            return self.query['task']
        except KeyError:
            raise self.logerr('No task specified.') from None

    @property
    def document(self):
        """Returns the appropriate statistics document"""
        try:
            return self.query['document']
        except KeyError:
            raise self.logerr('Document must not be null.') from None

    @property
    def pin(self):
        """Returns the cleaning PIN"""
        try:
            return int(self.query['pin'])
        except KeyError:
            raise self.logerr('No PIN provided.') from None
        except (TypeError, ValueError):
            raise self.logerr('PIN must be an integer.') from None

    def _get_url(self, url):
        """Proxies the respective URL"""
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

    def get(self):
        """Handles GET requests"""
        if self.resource == 'command':
            return self.list_commands(self.customer, self.vid)
        elif self.resource == 'cleaning':
            return self.list_cleanings(self.terminal)
        else:
            raise self.logerr('Invalid operation.') from None

    def post(self):
        """Handles POST requests"""
        if self.resource == 'command':
            return self.complete_command(self.customer, self.vid, self.task)
        elif self.resource == 'statistics':
            return self.add_statistics(
                self.customer, self.vid, self.tid, self.document)
        elif self.resource == 'cleaning':
            return self.add_cleaning(self.terminal, self.pin)
        elif self.resource == 'proxy':
            return self.proxy()
        else:
            raise self.logerr('Invalid operation.') from None

    def list_commands(self, customer, vid):
        """Lists commands for the respective terminal"""
        tasks = []

        for command in Command.select().where(
                (Command.customer == customer) &
                (Command.vid == vid) &
                (Command.completed >> None)):
            tasks.append(command.task)

        return JSON(tasks)

    def list_cleanings(self, terminal):
        """Lists cleaning entries for the respective terminal"""
        try:
            address = terminal.location.address
        except AttributeError:
            raise self.logerr('Terminal has no address.') from None
        else:
            return JSON(CleaningDate.of(address, limit=10))

    def complete_command(self, customer, vid, task):
        """Completes the provided command"""
        result = False

        for command in Command.select().where(
                (Command.customer == customer) &
                (Command.vid == vid) &
                (Command.task == task) &
                (Command.completed >> None)):
            command.complete()
            result = True

        return OK('1' if result else '0')

    def add_statistics(self, customer, vid, tid, document):
        """Adds a new statistics entry"""
        try:
            Statistics.add(customer, vid, tid, document)
        except Exception as e:
            raise InternalServerError(str(e)) from None
        else:
            return OK(status=201)

    def add_cleaning(self, terminal, pin):
        """Adds a cleaning entry"""
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

    def proxy(self):
        """Proxies URLs"""
        try:
            url = urlparse(self.data.decode())
        except AttributeError:
            raise self.logerr('No data provided.') from None
        except ValueError:
            raise self.logerr('Provided data is not UTF-8 URL.') from None
        else:
            if url.scheme in ('http', 'https'):
                if url.hostname != '':
                    try:
                        ProxyHost.get(ProxyHost.hostname == url.hostname)
                    except DoesNotExist:
                        raise self.logerr(
                            'Host name is not whitelisted.',
                            status=403) from None
                    else:
                        return self._get_url(url.geturl())
                else:
                    raise self.logerr('Host name must not be empty.') from None
            else:
                raise self.logerr('Scheme must be HTTP or HTTPS.') from None
