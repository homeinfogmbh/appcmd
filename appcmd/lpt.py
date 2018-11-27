"""Local public transportation API."""

from json import load
from logging import getLogger

from timelib import isoformat, strpdatetime
from trias import Client as TriasClient
from hafas import Client as HafasClient
from wsgilib import ACCEPT, JSON, XML

from appcmd.functions import get_terminal
from appcmd.dom import lpt as dom


__all__ = ['get_departures']


CONFIG_FILE = '/etc/lpt.json'


def _load_clients_map():
    """Loads the clients map."""

    logger = getLogger('LPT')

    with open(CONFIG_FILE, 'r') as file:
        json = load(file)

    for name, config in json.items():
        logger.info('Loading %s.', name)

        try:
            type_ = config['type'].strip().lower()
        except KeyError:
            logger.error('No type specified.')
            continue

        try:
            url = config['url']
        except KeyError:
            logger.error('No URL specified.')
            continue

        if type_ == 'trias':
            try:
                requestor_ref = config['requestor_ref']
            except KeyError:
                logger.error('No requestor_ref specified.')
                continue

            debug = config.get('debug', False)
            client = TriasClient(url, requestor_ref, debug=debug)
        elif type_ == 'hafas':
            try:
                access_id = config['access_id']
            except KeyError:
                logger.error('No access_id specified.')
                continue

            client = HafasClient(url, access_id)
        else:
            logger.error('Invalid client type: "%s".', type_)
            continue

        for (start, end) in config.get('zip_codes'):
            for zip_code in range(start, end+1):
                yield (zip_code, client)


try:
    CLIENTS = dict(_load_clients_map())
except FileNotFoundError:
    CLIENTS = {}


def get_departures_trias(client, address):
    """Returns departures from the respective Trias client."""

    longitude, latitude = client.geocoordinates(repr(address))
    trias = client.stops(longitude, latitude)
    payload = trias.ServiceDelivery.DeliveryPayload
    stops = []

    for location in payload.LocationInformationResponse.Location:
        stop_point_ref = location.Location.StopPoint.StopPointRef
        trias = client.stop_event(stop_point_ref)
        payload = trias.ServiceDelivery.DeliveryPayload
        stop_events = []

        for stop_event_result in payload.StopEventResult:
            stop_event = StopEvent.from_trias(stop_event_result)
            stop_events.append(stop_event)

        stop = Stop.from_trias(location, stop_events)
        stops.append(stop)

    return stops


def get_departures_hafas(client, address):
    """Returns departures from the respective HAFAS client."""

    location_list = client.locations(repr(address))
    stops = []

    for stop_location in location_list.StopLocation:
        departure_board = client.departure_board(stop_location.id)
        stop_events = []

        for departure in departure_board.Departure:
            stop_event = StopEvent.from_hafas(departure)
            stop_events.append(stop_event)

        stop = Stop.from_hafas(stop_location, stop_events)
        stops.append(stop)

    return stops


def get_departures():
    """Returns a list of departures."""

    terminal = get_terminal()
    address = terminal.address

    if address is None:
        return ('Terminal has no address.', 400)

    try:
        client = CLIENTS[address.zip_code]
    except KeyError:
        return ('No client for ZIP code "{}".'.format(address.zip_code), 400)

    if isinstance(client, TriasClient):
        stops = get_departures_trias(client, address)
    elif isinstance(client, HafasClient):
        stops = get_departures_hafas(client, address)
    else:
        return ('Invalid client "{}".'.format(type(client).__name__), 400)

    if 'application/json' in ACCEPT:
        return JSON([stop.to_json() for stop in stops])

    xml = dom.stops()
    xml.stop = [stop.to_dom() for stop in stops]
    return XML(xml)


class Stop:
    """Represents stops."""

    __slots__ = ('ident', 'name', 'longitude', 'latitude', 'stop_events')

    def __init__(self, ident, name, longitude, latitude, stop_events=()):
        """Creates a new stop."""
        self.ident = ident
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.stop_events = stop_events or []

    @classmethod
    def from_trias(cls, location, stop_events=()):
        """Creates a stop from the respective
        Trias
            → ServiceDelivery
                → DeliveryPayload
                    → LocationInformationResponse
                        → Location
        node from a location information response.
        """
        ident = location.Location.StopPoint.StopPointRef
        name = location.Location.StopPoint.StopPointName.Text
        longitude = location.Location.GeoPosition.Longitude
        latitude = location.Location.GeoPosition.Latitude
        return cls(ident, name, longitude, latitude, stop_events=stop_events)

    @classmethod
    def from_hafas(cls, stop_location, stop_events=()):
        """Creates a stop from the respective HAFAS CoordLocation element."""
        ident = stop_location.id
        name = stop_location.name
        latitude = stop_location.lat
        longitude = stop_location.lon
        return cls(ident, name, longitude, latitude, stop_events)

    def to_json(self):
        """Returns a JSON-ish dict."""
        return {
            'ident': self.ident,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'stop_events': [
                stop_event.to_json() for stop_event in self.stop_events]}

    def to_dom(self):
        """Returns an XML DOM."""
        stop = dom.Stop()
        stop.ident = self.ident
        stop.name = self.name
        stop.latitude = self.latitude
        stop.longitude = self.longitude
        stop.stop_event = [
            stop_event.to_dom() for stop_event in self.stop_events]
        return stop


class StopEvent:
    """Represents stop events."""

    __slots__ = ('line', 'scheduled', 'estimated', 'destination', 'route')

    def __init__(self, line, scheduled, estimated, destination, route=None):
        """Sets the, line name, scheduled and estimated departure,
        destination of line and an optional route description.
        """
        self.line = line
        self.scheduled = scheduled
        self.estimated = estimated
        self.destination = destination
        self.route = route

    @classmethod
    def from_trias(cls, stop_event_result):
        """Creates a stop event from the respective
        Trias
            → DeliveryPayload
                → StopEventResponse
                    → StopEventResult
        node from a stop event.response.
        """
        line = stop_event_result.StopEvent.Service.PublishedLineName.Text
        _this_call = stop_event_result.StopEvent.ThisCall
        scheduled = _this_call.CallAtStop.ServiceDeparture.TimetabledTime
        estimated = _this_call.CallAtStop.ServiceDeparture.EstimatedTime
        destination = stop_event_result.StopEvent.Service.DestinationText.Text
        route = stop_event_result.StopEvent.Service.RouteDescription.Text
        return cls(line, scheduled, estimated, destination, route=route)

    @classmethod
    def from_hafas(cls, departure):
        """Creates a stop from the respective HAFAS Departure element."""
        line = departure.Product.line
        scheduled = '{}T{}'.format(departure.date, departure.Time)
        scheduled = strpdatetime(scheduled)
        estimated = '{}T{}'.format(departure.rtDate, departure.rtTime)
        estimated = strpdatetime(estimated)
        destination = departure.direction
        return cls(line, scheduled, estimated, destination)

    def to_json(self):
        """Returns a JSON-ish dict."""
        return {
            'line': self.line,
            'scheduled': self.scheduled.isoformat(),
            'estimated': isoformat(self.estimated),
            'destination': self.destination,
            'route': self.route}

    def to_dom(self):
        """Returns an XML DOM."""
        stop_event = dom.StopEvent()
        stop_event.line = self.line
        stop_event.scheduled = self.scheduled
        stop_event.estimated = self.estimated
        stop_event.destination = self.destination
        stop_event.route = self.route
        return stop_event