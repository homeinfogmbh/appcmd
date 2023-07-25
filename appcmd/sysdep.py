"""Return information about the system and deployment."""

from wsgilib import JSON

from appcmd.functions import get_deployment


__all__ = ["deployment_info"]


def deployment_info() -> JSON:
    """Returns information about the system's deployment."""

    return JSON(get_deployment().to_json(cascade=2))
