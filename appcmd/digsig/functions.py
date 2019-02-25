"""Functions for digital signage aggregation."""

from hashlib import sha256
from io import BytesIO
from json import dumps
from tarfile import open as tar_open, TarInfo
from tempfile import TemporaryFile

from flask import request, Response

from mimeutil import FileMetaData


__all__ = ['make_attachment', 'stream_tared_files']


def make_attachment(bytes_):
    """Returns the respective attachment's name."""

    return (FileMetaData.from_bytes(bytes_).filename, bytes_)


def _tar_file(tarfile, filename, bytes_):
    """Adds the respective bytes to the tar file."""

    tarinfo = TarInfo(filename)
    tarinfo.size = len(bytes_)
    file = BytesIO(bytes_)
    tarfile.addfile(tarinfo, file)


def get_difftar_stream(files, sha256sums, *, chunk_size=4096):
    """Adds the respective files to a tar archive."""

    manifest = []

    with TemporaryFile(mode='w+b') as tmp:
        with tar_open(mode='w:xz', fileobj=tmp) as tar:
            for filename, bytes_ in files:
                manifest.append(filename)

                if sha256(bytes_).hexdigest() not in sha256sums:
                    _tar_file(tar, filename, bytes_)

            manifest = dumps(manifest).encode()
            _tar_file(tar, 'manifest.json', manifest)

        tmp.flush()
        tmp.seek(0)
        chunk = tmp.read(chunk_size)

        while chunk:
            yield chunk
            chunk = tmp.read(chunk_size)


def stream_tared_files(files, *, chunk_size=4096):
    """Streams the respective tar file."""

    sha256sums = frozenset(request.json or ())
    stream = get_difftar_stream(files, sha256sums, chunk_size=chunk_size)
    return Response(stream, mimetype='application/x-xz')
