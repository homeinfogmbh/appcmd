"""Interface to participate in DSMCS4 polls."""

from cmslib.orm.charts.poll import Mode, Poll, Option
from wsgilib import Error

from appcmd.functions import get_json


__all__ = ['cast_vote']


def cast_vote():
    """Vote for a respective poll."""

    json = get_json()

    try:
        poll = json['poll']
    except KeyError:
        raise Error('No poll ID specified.')

    try:
        poll = Poll[poll]
    except Poll.DoesNotExist:
        raise Error('No such poll.', status=404)

    if not poll.base.active:
        raise Error('Poll is not active.')

    choices = json.get('choices')

    if not choices:
        raise Error('No choice provided.')

    if not isinstance(choices, list):
        raise Error('Choices is not a list.')

    if poll.mode == Mode.SINGLE_CHOICE and len(choices) > 1:
        raise Error('Only one option is allowed in single choice mode.')

    options = []

    for choice in choices:
        try:
            option = Option.get((Option.poll == poll) & (Option.id == choice))
        except Option.DoesNotExist:
            raise Error(f'No option #{choice} for poll #{poll.id}.',
                        status=404)

        options.append(option)

    for option in options:
        option.votes += 1
        option.save()

    return 'Vote casted.'
