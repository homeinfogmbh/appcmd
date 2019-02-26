"""Functions for digital signage aggregation."""

from functools import partial
from hashlib import sha256
from io import BytesIO
from json import dumps
from mimetypes import guess_extension
from tarfile import open as tar_open, TarInfo
from tempfile import TemporaryFile

from flask import request, Response

from hisfs import File


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


def _tar_file(tarfile, filename, file_handler):
    """Adds the file to the tar archive."""

    tarinfo = TarInfo(filename)
    tarfile.addfile(tarinfo, file_handler)


def _tar_files(tarfile, files, manifest, *, chunk_size=4096):
    """Adds the files tot the tar archive."""

    file_list = []

    for filename, file in files:
        file_list.append(filename)

        if manifest.get(filename) == _sha256sum(file):
            continue

        if isinstance(file, File):
            with File.open('rb', chunk_size=chunk_size) as file_handler:
                _tar_file(tarfile, filename, file_handler)
        elif isinstance(file, bytes):
            _tar_file(tarfile, filename, BytesIO(file))
        else:
            raise ValueError('Unsupported file type: %s.' % type(file))

    file_list = dumps(file_list).encode()
    _tar_file(tarfile, 'manifest.json', file_list)


def difftar_stream(files, manifest, *, chunk_size=4096):
    """Adds files that have been changed to a tar.xz
    archive and streams its bytes chunk-wise.
    """

    with TemporaryFile(mode='w+b') as tmp:
        with tar_open(mode='w:xz', fileobj=tmp) as tar:
            _tar_files(tar, files, manifest)

        tmp.flush()
        tmp.seek(0)

        for chunk in iter(partial(tmp.read, chunk_size), b''):
            yield chunk


def stream_tar_xz(files, *, chunk_size=4096):
    """Returns a streams of tar.xz'ed files."""

    manifest = request.json or {}
    stream = difftar_stream(files, manifest, chunk_size=chunk_size)
    return Response(stream, mimetype='application/x-xz')
