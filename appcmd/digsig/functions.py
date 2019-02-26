"""Functions for digital signage aggregation."""

from hashlib import sha256
from io import BytesIO
from json import dumps
from tarfile import open as tar_open, TarInfo
from tempfile import TemporaryFile

from flask import request, Response

from mimeutil import FileMetaData


__all__ = ['make_attachment', 'stream_tar_xz']


def make_attachment(bytes_):
    """Returns the respective attachment's name."""

    return (FileMetaData.from_bytes(bytes_).filename, bytes_)


def _tar_file(tarfile, filename, bytes_):
    """Adds the respective file to the tar archive."""

    tarinfo = TarInfo(filename)
    tarinfo.size = len(bytes_)
    file = BytesIO(bytes_)
    tarfile.addfile(tarinfo, file)


def difftar_stream(files, manifest, *, chunk_size=4096):
    """Adds files that have been changed to a tar.xz
    archive and streams its bytes chunk-wise.
    """

    file_list = []

    with TemporaryFile(mode='w+b') as tmp:
        with tar_open(mode='w:xz', fileobj=tmp) as tar:
            for filename, bytes_ in files:
                file_list.append(filename)
                sha256sum = manifest.get(filename)

                if sha256(bytes_).hexdigest() != sha256sum:
                    _tar_file(tar, filename, bytes_)

            file_list = dumps(file_list).encode()
            _tar_file(tar, 'manifest.json', file_list)

        tmp.flush()
        tmp.seek(0)
        chunk = tmp.read(chunk_size)

        while chunk:
            yield chunk
            chunk = tmp.read(chunk_size)


def stream_tar_xz(files, *, chunk_size=4096):
    """Returns a streams of tar.xz'ed files."""

    manifest = request.json or {}
    stream = difftar_stream(files, manifest, chunk_size=chunk_size)
    return Response(stream, mimetype='application/x-xz')
