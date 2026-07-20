"""Format-Registry: löst den Config-Namen auf einen Formatter auf."""

from __future__ import annotations

from .base import ChangelogFormatter, FormatError
from .conventional import ConventionalFormatter
from .keep_a_changelog import KeepAChangelogFormatter
from .smart import SmartFormatter

_FORMATTERS: dict[str, type[ChangelogFormatter]] = {
    KeepAChangelogFormatter.name: KeepAChangelogFormatter,
    ConventionalFormatter.name: ConventionalFormatter,
    SmartFormatter.name: SmartFormatter,
}


def available_formats() -> list[str]:
    """Return the list of known format names."""
    return list(_FORMATTERS.keys())


def get_formatter(name: str, prefix: str = "") -> ChangelogFormatter:
    """Resolve a formatter by name. Unknown names raise a clear German error."""
    cls = _FORMATTERS.get(name)
    if cls is None:
        raise FormatError(
            "Unbekanntes Format '" + str(name) + "'. Verfügbar: "
            + ", ".join(available_formats()) + ". Lösung: eines dieser Formate "
            "in der Konfiguration eintragen."
        )
    return cls(prefix=prefix)
