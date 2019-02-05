"""Local public transportation API."""

from datetime import datetime, timedelta

from flask import request
from lptlib import dom, get_departures as _get_departures, Stop, StopEvent
from wsgilib import ACCEPT, JSON, XML

from appcmd.functions import get_terminal


__all__ = ['get_departures']


def _get_departures_test():
    """Returns a test set of departures."""

    now = datetime.now()
    on_time = StopEvent('18', now, None, 'Istanbul', 'S-Bahn')
    on_time_explicit = StopEvent('Pünklicher Bus', now, now, 'Katwijk', 'Bus')
    delay = timedelta(minutes=42)
    delayed = StopEvent('Verspätetet', now, now + delay, 'Bonn', 'Fliewatüüt')
    early = StopEvent('Überpünklich', now, now - delay, 'Berlin', 'Pferd')
    departures = (on_time, on_time_explicit, delayed, early)
    stop = Stop('Nächstgelegene Haltestelle', 'Nächstgelegene Haltestelle',
                -38.2626511, 144.5796318, departures)
    return [stop]


def get_departures():
    """Returns the respective departures."""

    if 'test' in request.args:
        stops = _get_departures_test()
    else:
        stops = _get_departures(get_terminal().address)

    if 'application/json' in ACCEPT:
        return JSON([stop.to_json() for stop in stops])

    xml = dom.stops()
    xml.stop = [stop.to_dom() for stop in stops]
    return XML(xml)
