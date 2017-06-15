"""ORM models"""

from datetime import datetime
from peewee import DoesNotExist, Model, PrimaryKeyField, ForeignKeyField, \
    TextField, DateTimeField, BooleanField, IntegerField, CharField

from homeinfo.crm import Customer
from homeinfo.terminals.orm import Terminal
from peeweeplus import MySQLDatabase


database = MySQLDatabase('application')


class ApplicationModel(Model):
    """Abstract common model"""

    class Meta:
        database = database
        schema = database.database

    id = PrimaryKeyField()


class TenantMessage(ApplicationModel):
    """Tenant to tenant messages"""

    terminal = ForeignKeyField(Terminal, db_column='terminal')
    message = TextField()
    created = DateTimeField()
    released = BooleanField(default=False)
    start_date = DateTimeField(null=True, default=None)
    end_date = DateTimeField(null=True, default=None)

    @classmethod
    def add(cls, terminal, message):
        """Creates a new entry for the respective terminal"""
        record = cls()
        record.terminal = terminal
        record.message = message
        record.created = datetime.now()
        record.save()
        return record


class Command(ApplicationModel):
    """Command entries"""

    customer = ForeignKeyField(Customer, db_column='customer')
    vid = IntegerField()
    task = CharField(16)
    created = DateTimeField()
    completed = DateTimeField(null=True, default=None)

    @classmethod
    def add(cls, customer, vid, task):
        """Creates a new task"""
        try:
            return cls.get(
                (cls.customer == customer) & (cls.vid == vid) &
                (cls.task == task))
        except DoesNotExist:
            record = cls()
            record.customer = customer
            record.vid = vid
            record.task = task
            record.created = datetime.now()
            record.save()
            return record

    def complete(self, force=False):
        """Completes the command"""
        if force or self.completed is None:
            self.completed = datetime.now()
            self.save()
