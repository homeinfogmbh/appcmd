"""Error handling."""

from tempfile import NamedTemporaryFile
from traceback import format_exc


__all__ = ['log_error']


def log_error(exception):
    """Logs the respective exception."""

    with NamedTemporaryFile(mode='w', suffix='.stacktrace') as tmp:
        tmp.write(format_exc())
        tmp.write('\n')
        tmp.write(str(exception))

    print('Wrote stack trace to:', tmp.name, flush=True)
