"""Legacy command interface for Smart TVs."""

from flask import request

from digsigdb import Command
from wsgilib import JSON, XML

from appcmd import dom
from appcmd.functions import get_customer


__all__ = ['list_commands', 'complete_command']


def _response(commands_):
    """Returns an XML or JSON response."""
    content_type = request.headers.get('Accept', 'application/json')

    if content_type == 'application/xml':
        commands = dom.commands.commands()

        for command in commands_:
            commands.task.append(command.task)

        return XML(commands)

    if content_type == 'application/json':
        return JSON([command.task for command in commands_])

    return ('Invalid content type.', 406)


def list_commands():
    """Lists commands for the respective terminal."""

    commands = Command.select().where(
        (Command.customer == get_customer())
        & (Command.vid == request.args['vid'])
        & (Command.completed >> None))
    return _response(commands)


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
