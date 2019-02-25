"""Functions for digital signage aggregation."""

from functools import partial
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


def tar_file(tarfile, filename, bytes_):
    """Adds the respective bytes to the tar file."""

    tarinfo = TarInfo(filename)
    tarinfo.size = len(bytes_)
    file = BytesIO(bytes_)
    tarfile.addfile(tarinfo, file)


def get_tar_stream(files, *, chunk_size=4096):
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
        yield from iter(partial(tmp.read, chunk_size), b'')


def stream_tared_files(files, *, chunk_size=4096):
    """Streams the respective tar file."""

    headers = {'Content-Type': 'application/x-xz'}
    stream = get_tar_stream(files, chunk_size=chunk_size)
    return Response(stream, headers=headers)
