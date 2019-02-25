"""Functions for digital signage aggregation."""

from hashlib import sha256
from io import BytesIO
from json import dumps
from tarfile import open as tar_open, TarInfo
from tempfile import TemporaryFile

from flask import make_response, request, Response

from mimeutil import FileMetaData


__all__ = ['make_attachment', 'tar_files']


def make_attachment(bytes_):
    """Returns the respective attachment's name."""

    return (FileMetaData.from_bytes(bytes_).filename, bytes_)


def tar_files(files):
    """Adds the respective files to a tar archive."""

    sha256sums = frozenset(request.json or ())
    manifest = []
    empty = True

    with TemporaryFile(mode='w+b') as tmp:
        with tar_open(mode='w:xz', fileobj=tmp) as tar:
            for filename, bytes_ in files:
                manifest.append(filename)

                if sha256(bytes_).hexdigest() in sha256sums:
                    continue

                empty = False
                tarinfo = TarInfo(filename)
                tarinfo.size = len(bytes_)
                file = BytesIO(bytes_)
                tar.addfile(tarinfo, file)

        if empty:
            return Response(
                dumps(manifest).encode(), status=304,
                content_type='application/json')

        tmp.flush()
        tmp.seek(0)
        response = make_response(tmp.read())
        response.headers.set('Content-Type', 'application/x-xz')
        return response
