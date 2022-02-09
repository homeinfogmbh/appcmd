"""Endpoint for systems to check whether they are online."""


__all__ = ['online_check']


def online_check() -> str:
    """Return a dummy message."""

    return "Congratulations, you're online."
