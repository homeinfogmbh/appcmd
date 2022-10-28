"""Interface to participate in DSMCS4 polls."""

from typing import Iterable, Iterator

from cmslib import Poll, PollMode, PollOption
from wsgilib import Error

from appcmd.functions import get_json


__all__ = ['cast_vote']


def get_poll(json: dict) -> Poll:
    """Returns the respective poll."""

    try:
        poll = json['poll']
    except KeyError:
        raise Error('No poll ID specified.') from None

    try:
        poll = Poll[poll]
    except Poll.DoesNotExist:
        raise Error('No such poll.', status=404) from None

    if not poll.base.active:
        raise Error('Poll is not active.')

    return poll


def get_choices(json: dict, mode: PollMode) -> list[int]:
    """Returns the choices for the respective poll."""

    if not (choices := json.get('choices')):
        raise Error('No choice provided.')

    if not isinstance(choices, list):
        raise Error('Choices is not a list.')

    if mode == PollMode.SINGLE_CHOICE and len(choices) > 1:
        raise Error('Only one option is allowed in single choice mode.')

    return choices


def get_poll_and_choices(json: dict) -> tuple[Poll, list[int]]:
    """Returns the poll and choices."""

    return (poll := get_poll(json)), get_choices(json, poll.mode)


def get_options(poll: Poll, choices: Iterable[int]) -> Iterator[PollOption]:
    """Gets the corresponding poll options for the given choices."""

    for choice in choices:
        try:
            yield PollOption.select().where(
                (PollOption.poll == poll) & (PollOption.id == choice)
            ).get()
        except PollOption.DoesNotExist:
            message = f'Invalid choice {choice} for poll {poll.id}.'
            raise Error(message, status=404) from None


def cast_vote() -> str:
    """Vote for a respective poll."""

    poll, choices = get_poll_and_choices(get_json())

    for option in get_options(poll, choices):
        option.vote()

    return 'Vote casted.'
