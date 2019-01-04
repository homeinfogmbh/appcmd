"""Interface to participate in DSMCS4 polls."""

from dscms4.orm.charts import Poll, PollMode, PollOption
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

    choices = json.get('choices')

    if not choices:
        raise Error('No choice provided.')
    elif not isinstance(choices, list):
        raise Error('Choices is not a list.')

    if poll.mode == PollMode.SINGLE_CHOICE and len(choices) > 1:
        raise Error('Only one option is allowed in single choice mode.')

    options = []

    for choice in choices:
        try:
            option = PollOption.get(
                (PollOption.poll == poll) & (PollOption.id == choice))
        except PollOption.DoesNotExist:
            raise Error('No such option "{}" for poll "{}".'.format(
                choice, poll.id))

        options.append(option)

    for option in options:
        option.votes += 1
        option.save()

    return 'Vote casted.'
