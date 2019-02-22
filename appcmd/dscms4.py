"""Provides DSCMS4 data."""

from io import BytesIO
from tarfile import open as TarFile, TarInfo
from tempfile import TemporaryFile

from flask import make_response
from requests.exceptions import MissingSchema

from cmslib.exceptions import AmbiguousConfigurationsError
from cmslib.exceptions import FeedReadError
from cmslib.exceptions import NoConfigurationFound
from cmslib.orm.charts import RSS
from cmslib.presentation.terminal import Presentation
from hisfs import File
from mimeutil import FileMetaData
from wsgilib import Error

from appcmd.functions import get_terminal, changed_files
from appcmd.logger import LOGGER


LOGGER = LOGGER.getChild('DSCMS4')


def _rss_charts(charts):
    """Yields RSS feed charts."""

    for chart in charts:
        if isinstance(chart, RSS):
            yield chart


def _make_attachment(bytes_):
    """Returns the respective attachment's name."""

    return (FileMetaData.from_bytes(bytes_).filename, bytes_)


def _get_files(terminal):
    """Yields files for the respective terminal."""

    presentation = Presentation(terminal)

    try:
        presentation_dom = presentation.to_dom()
    except AmbiguousConfigurationsError:
        message = 'Ambiguous configurations for terminal.'
        LOGGER.error(message)
        raise Error(message, status=420)
    except NoConfigurationFound:
        message = 'No configuration for terminal.'
        LOGGER.error(message)
        raise Error(message, status=420)

    presentation_bytes = presentation_dom.toxml(encoding='utf-8')
    yield ('presentation.xml', presentation_bytes)

    # Aggregate files.
    for file_id in presentation.files:
        try:
            file = File.get(File.id == file_id)
        except File.DoesNotExist:
            LOGGER.error('File not found: %i.', file_id)
            continue

        yield _make_attachment(file.bytes)

    # Aggregate RSS feeds.
    for chart in _rss_charts(presentation.charts):
        try:
            feed = chart.feed
        except MissingSchema:
            LOGGER.error('Could not add RSS feed. Missing schema.')
            continue
        except FeedReadError:
            LOGGER.error('Could not retrieve feed.')
            continue

        filename = 'feed-{}.rss'.format(chart.id)
        yield(filename, feed.encode())


def get_presentation_package():
    """Returns the presentation and associated
    data for the respective terminal.
    """

    terminal = get_terminal()

    with TemporaryFile('w+b') as tmp:
        with TarFile(tmp, 'w:xz') as tar:
            empty = True
            files = _get_files(terminal)

            for filename, bytes_ in changed_files(files):
                empty = False
                tarinfo = TarInfo(filename)
                tarinfo.size = len(bytes_)
                file = BytesIO(bytes)
                tar.addfile(tarinfo, file)

        if empty:
            return ('Nothing to do.', 304)

        tmp.flush()
        response = make_response(tmp.read())
        response.headers.set('Content-Type', 'application/x-xz')
        return response
