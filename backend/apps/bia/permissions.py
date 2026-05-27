"""BIA reuses the CEA permission shape — same edit/view matrix per the brief."""

from apps.cea.permissions import CEAPermission as _CEAPermission


class BIAPermission(_CEAPermission):
    """Aliased class so DRF Browsable API displays a meaningful name."""

    pass
