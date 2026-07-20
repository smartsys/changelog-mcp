"""Format 'smart' (freie Kategorien)."""

from __future__ import annotations

from .base import ChangelogFormatter


class SmartFormatter(ChangelogFormatter):
    """smart preset: [X.Y.Z] - YYYY-MM-DD, akzeptiert jede Kategorie.

    Die empfohlenen Kategorien dienen nur als Vorschlagsliste.
    """

    name = "smart"
    # Versions-Überschrift im keep-a-changelog-Stil (## [x.y.z] - Datum).
    categories = (
        "Added",
        "Changed",
        "Deprecated",
        "Removed",
        "Fixed",
        "Security",
        "Documentation",
    )
    strict = False

    def version_heading(self, version: str, date: str) -> str:
        return "## [" + self._v(version) + "] - " + date

    def format_initial_changelog(self) -> str:
        return "# Changelog\n"
