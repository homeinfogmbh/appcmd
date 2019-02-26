"""Functions for digital signage aggregation."""

from hashlib import sha256
from json import dumps
from mimetypes import guess_extension
from tarfile import open as tar_open, TarInfo
from tempfile import TemporaryFile

from flask import request, Response

from hisfs import File, NamedFileStream


__all__ = ['make_attachment', 'stream_tar_xz']


def make_attachment(file):
    """Returns the respective attachment's name."""

    return (file.sha256sum + guess_extension(file.mimetype), file)


def _sha256sum(file):
    """Returns the respective SHA-256 sum."""

    if isinstance(file, File):
        return file.sha256sum

    if isinstance(file, bytes):
        return sha256(file).hexdigest()

    raise ValueError('Unsupported file type: %s.' % type(file))


def _tar_stream(tarfile, stream):
    """Adds the file to the tar archive."""

    tarinfo = TarInfo(stream.name)
    tarinfo.size = stream.size
    tarfile.addfile(tarinfo, stream.file)


def _tar_streams(tarfile, streams, manifest):
    """Adds the files tot the tar archive."""

    file_list = []

    for stream in streams:
        file_list.append(stream.name)

        if manifest.get(stream.name) == stream.sha256sum:
            continue

        _tar_stream(tarfile, stream)

    file_list = dumps(file_list).encode()
    stream = NamedFileStream.from_bytes(file_list, name='manifest.json')
    _tar_stream(tarfile, stream)


def difftar_stream(streams, manifest):
    """Adds files that have been changed to a tar.xz
    archive and streams its bytes chunk-wise.
    """

    with TemporaryFile(mode='w+b') as tmp:
        with tar_open(mode='w:xz', fileobj=tmp) as tar:
            _tar_streams(tar, streams, manifest)

        tmp.flush()
        tmp.seek(0)

        for chunk in iter(tmp.read, b''):
            yield chunk


def stream_tar_xz(streams):
    """Returns a streams of tar.xz'ed files."""

    manifest = request.json or {}
    stream = difftar_stream(streams, manifest)
    return Response(stream, mimetype='application/x-xz')
