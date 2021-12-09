"""Website proxy service."""

from urllib.parse import urlparse

from flask import request, Response
from requests import get

from digsigdb import ProxyHost


__all__ = ['proxy']


ALLOWED_SCHEMES = {'http', 'https'}


def proxy() -> Response:
    """Proxies URLs."""

    url = urlparse(request.get_data().decode())

    if url.scheme not in ALLOWED_SCHEMES:
        return ('URL scheme not allowed.', 400)

    if not url.hostname:
        return ('Host name must not be empty.', 400)

    # Avoid SSRF.
    try:
        ProxyHost.get(ProxyHost.hostname == url.hostname)
    except ProxyHost.DoesNotExist:
        return ('Host name is not whitelisted.', 403)

    reply = get(url.geturl())
    return Response(
        reply.content, status=reply.status_code,
        content_type=reply.headers['Content-Type'])
