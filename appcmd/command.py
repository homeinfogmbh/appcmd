"""Legacy command interface for Smart TVs."""

from flask import request

from digsigdb import Command
from wsgilib import JSON

from appcmd.functions import get_customer

__all__ = ['list_commands', 'complete_command']


def list_commands():
    """Lists commands for the respective terminal."""

    customer = get_customer()
    tasks = []

    for command in Command.select().where(
            (Command.customer == customer)
            & (Command.vid == request.args['vid'])
            & (Command.completed >> None)):
        tasks.append(command.task)

    return JSON(tasks)


def complete_command():
    """Completes the provided command."""

    result = False

    for command in Command.select().where(
            (Command.customer == get_customer())
            & (Command.vid == request.args['vid'])
            & (Command.task == request.args['task'])
            & (Command.completed >> None)):
        command.complete()
        result = True

    return str(int(result))
