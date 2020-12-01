"""Common stuff."""

from __future__ import annotations
from datetime import datetime
from functools import total_ordering
from hashlib import sha256
from os.path import getctime
from pathlib import Path
from typing import NamedTuple

from flask import request

from wsgilib import Error


__all__ = ['FileInfo']


@total_ordering
class FileInfo(NamedTuple):
    """Represents file status information."""

    sha256sum: str
    ctime: datetime

    def __eq__(self, other: FileInfo) -> bool:
        """Determines whether a file is considered newer than the other."""
        return self.sha256sum == other.sha256sum

    def __gt__(self, other: FileInfo) -> bool:
        """Determines whether a file is considered newer than the other."""
        if self == other:
            return False

        return self.ctime > other.ctime

    @classmethod
    def from_request(cls) -> FileInfo:
        """Returns the file info from the current request context."""
        json = request.json

        if json is None:
            raise Error('Outdated protocol.', status=204)

        sha256sum = json.get('sha256sum')

        if sha256sum is None:
            raise Error('No SHA-256 sum provided.', status=400)

        ctime = json.get('ctime')

        if ctime is None:
            raise Error('No CTIME provided.', status=400)

        return cls(sha256sum, datetime.fromtimestamp(ctime))

    @classmethod
    def from_file(cls, filename: Path) -> FileInfo:
        """Returns the file info from the provided file name or path."""
        with open(filename, 'rb') as file:
            sha256sum = sha256(file.read()).hexdigest()

        return cls(sha256sum, datetime.fromtimestamp(getctime(filename)))
