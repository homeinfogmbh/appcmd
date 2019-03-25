"""Statistics submission."""

from flask import request

from digsigdb import Statistics

from appcmd.functions import get_customer, get_terminal


__all__ = ['add_statistics']


def add_statistics(private=False):
    """Adds a new statistics entry."""

    if private:
        terminal = get_terminal()
        customer = terminal.customer
        tid = terminal.tid
        vid = terminal.vid
    else:
        customer = get_customer()
        tid = request.args.get('tid')
        vid = request.args['vid']

    Statistics.add(customer, vid, tid, request.args['document'])
    return ('Statistics added.', 201)
