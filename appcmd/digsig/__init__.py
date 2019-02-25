"""Digital signage synchronization endpoint."""

from appcmd.digsig.dscms4 import get_presentation_package


__all__ = ['get_digsig_pkg']


get_digsig_pkg = get_presentation_package   # TODO: For testing.
