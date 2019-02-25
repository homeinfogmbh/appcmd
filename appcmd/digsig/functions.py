"""Functions for digital signage aggregation."""

from functools import partial
from hashlib import sha256
from io import BytesIO
from json import dumps
from tarfile import open as tar_open, TarInfo
from tempfile import TemporaryFile

from flask import make_response, request

from mimeutil import FileMetaData


__all__ = ['make_attachment', 'tar_files']


def make_attachment(bytes_):
    """Returns the respective attachment's name."""

    return (FileMetaData.from_bytes(bytes_).filename, bytes_)


def tar_file(tarfile, filename, bytes_):
    """Adds the respective bytes to the tar file."""

    tarinfo = TarInfo(filename)
    tarinfo.size = len(bytes_)
    file = BytesIO(bytes_)
    tarfile.addfile(tarinfo, file)


def stream(file, chunk_size=4096):
    """Streams a file-like object."""

    yield from iter(partial(file.read, chunk_size), b'')


def tar_files(files):
    """Adds the respective files to a tar archive."""

    sha256sums = frozenset(request.json or ())
    manifest = []

    with TemporaryFile(mode='w+b') as tmp:
        with tar_open(mode='w:xz', fileobj=tmp) as tar:
            for filename, bytes_ in files:
                manifest.append(filename)

                if sha256(bytes_).hexdigest() in sha256sums:
                    continue

                tar_file(tar, filename, bytes_)

            manifest = dumps(manifest).encode()
            tar_file(tar, 'manifest.json', manifest)

        tmp.flush()
        tmp.seek(0)
        response = make_response(stream(tmp))
        response.headers.set('Content-Type', 'application/x-xz')
        return response
