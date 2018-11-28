"""Local public transportation API."""

from configparser import ConfigParser
from datetime import datetime
from json import load
from logging import getLogger

from timelib import isoformat, strpdatetime
from trias import Client as TriasClient
from hafas import Client as HafasClient
from wsgilib import ACCEPT, JSON, XML

from appcmd.functions import get_terminal
from appcmd.dom import lpt as dom


__all__ = ['get_departures']


CONFIG_FILE = '/etc/lpt.conf'
CONFIG = ConfigParser()
CONFIG.read(CONFIG_FILE)
MAX_STOPS = int(CONFIG['limits']['stops'])
MAX_DEPARTURES = int(CONFIG['limits']['departures'])
CLIENTS_CONFIG = '/etc/lpt.json'


def _load_clients_map():
    """Loads the clients map."""

    logger = getLogger('LPT')

    try:
        with open(CLIENTS_CONFIG, 'r') as file:
            json = load(file)
    except FileNotFoundError:
        logger.error('Config file "%s" not found.', CONFIG_FILE)
        return

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


CLIENTS = dict(_load_clients_map())


def get_departures_trias(client, address):
    """Returns departures from the respective Trias client."""

    longitude, latitude = client.geocoordinates(repr(address))
    trias = client.stops(longitude, latitude)
    payload = trias.ServiceDelivery.DeliveryPayload
    locations = payload.LocationInformationResponse.Location
    stops = []

    for stopc, location in enumerate(locations, start=1):
        if stopc > MAX_STOPS:
            break

        stop_point_ref = location.Location.StopPoint.StopPointRef.value()
        trias = client.stop_event(stop_point_ref)
        payload = trias.ServiceDelivery.DeliveryPayload
        stop_event_results = payload.StopEventResponse.StopEventResult
        departures = []

        for depc, stop_event_result in enumerate(stop_event_results, start=1):
            if depc > MAX_DEPARTURES:
                break

            departure = StopEvent.from_trias(stop_event_result)
            departures.append(departure)

        stop = Stop.from_trias(location, departures)
        stops.append(stop)

    return stops


def get_departures_hafas(client, address):
    """Returns departures from the respective HAFAS client."""

    location_list = client.locations(repr(address))
    stop_locations = location_list.StopLocation
    stops = []

    for stopc, stop_location in enumerate(stop_locations, start=1):
        if stopc > MAX_STOPS:
            break

        departure_board = client.departure_board(stop_location.id)
        departures = []

        for depc, departure in enumerate(departure_board.Departure, start=1):
            if depc > MAX_DEPARTURES:
                break

            departure = StopEvent.from_hafas(departure)
            departures.append(departure)

        stop = Stop.from_hafas(stop_location, departures)
        stops.append(stop)

    return stops


def get_departures():
    """Returns a list of departures."""

    terminal = get_terminal()
    address = terminal.address

    if address is None:
        return ('Terminal has no address.', 400)

    try:
        zip_code = int(address.zip_code)
    except TypeError:
        return ("No ZIP code specified in terminal's address.", 400)
    except ValueError:
        return ('ZIP code is not an integer.', 400)

    try:
        client = CLIENTS[zip_code]
    except KeyError:
        return ('No API available for ZIP code "{}".'.format(zip_code), 404)

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

    __slots__ = ('ident', 'name', 'longitude', 'latitude', 'departures')

    def __init__(self, ident, name, longitude, latitude, departures):
        """Creates a new stop."""
        self.ident = ident
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.departures = departures

    @classmethod
    def from_trias(cls, location, departures):
        """Creates a stop from the respective
        Trias
            → ServiceDelivery
                → DeliveryPayload
                    → LocationInformationResponse
                        → Location
        node from a location information response.
        """
        ident = str(location.Location.StopPoint.StopPointRef.value())
        name = str(location.Location.StopPoint.StopPointName.Text)
        longitude = float(location.Location.GeoPosition.Longitude)
        latitude = float(location.Location.GeoPosition.Latitude)
        return cls(ident, name, longitude, latitude, departures)

    @classmethod
    def from_hafas(cls, stop_location, departures):
        """Creates a stop from the respective HAFAS CoordLocation element."""
        ident = str(stop_location.id)
        name = str(stop_location.name)
        latitude = float(stop_location.lat)
        longitude = float(stop_location.lon)
        return cls(ident, name, longitude, latitude, departures)

    def to_json(self):
        """Returns a JSON-ish dict."""
        return {
            'ident': self.ident,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'departures': [
                departure.to_json() for departure in self.departures]}

    def to_dom(self):
        """Returns an XML DOM."""
        stop = dom.Stop()
        stop.ident = self.ident
        stop.name = self.name
        stop.latitude = self.latitude
        stop.longitude = self.longitude
        stop.departure = [departure.to_dom() for departure in self.departures]
        return stop


class StopEvent:
    """Represents stop events."""

    __slots__ = ('line', 'scheduled', 'estimated', 'destination', 'type')

    def __init__(self, line, scheduled, estimated, destination, type_):
        """Sets the, line name, scheduled and estimated departure,
        destination of line and an optional route description.
        """
        self.line = line
        self.scheduled = scheduled
        self.estimated = estimated
        self.destination = destination
        self.type = type_

    @classmethod
    def from_trias(cls, stop_event_result):
        """Creates a stop event from the respective
        Trias
            → DeliveryPayload
                → StopEventResponse
                    → StopEventResult
        node from a stop event.response.
        """
        _service = stop_event_result.StopEvent.Service
        line = str(_service.PublishedLineName.Text)
        _call_at_stop = stop_event_result.StopEvent.ThisCall.CallAtStop
        scheduled = _call_at_stop.ServiceDeparture.TimetabledTime
        scheduled = datetime.fromtimestamp(scheduled.timestamp())

        if _call_at_stop.ServiceDeparture.EstimatedTime is None:
            estimated = None
        else:
            estimated = _call_at_stop.ServiceDeparture.EstimatedTime
            estimated = datetime.fromtimestamp(estimated.timestamp())

        destination = str(_service.DestinationText.Text)

        try:
            route = _service.RouteDescription.Text
        except AttributeError:
            route = None
        else:
            route = str(route)

        type_ = str(_service.Mode.Name.Text)
        return cls(line, scheduled, estimated, destination, type_)

    @classmethod
    def from_hafas(cls, departure):
        """Creates a stop from the respective HAFAS Departure element."""
        line = str(departure.Product.line)
        scheduled = '{}T{}'.format(departure.date, departure.time)
        scheduled = strpdatetime(scheduled)

        if departure.rtTime is None:
            estimated = None
        else:
            estimated_date = departure.rtDate or departure.date
            estimated = '{}T{}'.format(estimated_date, departure.rtTime)
            estimated = strpdatetime(estimated)

        destination = str(departure.direction)
        type_ = str(departure.Product.catOutL)
        return cls(line, scheduled, estimated, destination, type_)

    def to_json(self):
        """Returns a JSON-ish dict."""
        return {
            'line': self.line,
            'scheduled': self.scheduled.isoformat(),
            'estimated': isoformat(self.estimated),
            'destination': self.destination,
            'type': self.type}

    def to_dom(self):
        """Returns an XML DOM."""
        stop_event = dom.StopEvent()
        stop_event.line = self.line
        stop_event.scheduled = self.scheduled
        stop_event.estimated = self.estimated
        stop_event.destination = self.destination
        stop_event.type = self.type
        return stop_event
