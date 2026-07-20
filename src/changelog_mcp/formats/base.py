"""Formatter-Protokoll und gemeinsame Render-Bausteine.

Jeder Formatter liefert: Kategorienliste, format_entry (Einzeleintrag für
CHANGELOG-full.md), format_release (kuratierter Block für CHANGELOG.md) und
format_initial_changelog (Header).
"""

from __future__ import annotations

from ..store.models import EntryRecord, ReleaseRecord


class FormatError(Exception):
    """Raised when a category is invalid for the active format."""


class ChangelogFormatter:
    """Base class for changelog formatters.

    Subclasses override name, categories, strict and version_heading.
    """

    name: str = "base"
    categories: tuple[str, ...] = ()
    strict: bool = False

    def __init__(self, prefix: str = "") -> None:
        # Anzeige-Prefix (z.B. 'v') aus der Config.
        self.prefix = prefix

    # -- Kategorien -------------------------------------------------------
    def validate_category(self, category: str) -> None:
        """Validate *category*. Strict formats reject unknown categories."""
        if not category or not category.strip():
            raise FormatError(
                "Leere Kategorie. Kontext: Format '" + self.name + "'. "
                "Lösung: eine gültige Kategorie angeben."
            )
        if self.strict and category not in self.categories:
            allowed = ", ".join(self.categories)
            raise FormatError(
                "Ungültige Kategorie '" + category + "' für Format '" + self.name
                + "'. Erlaubt: " + allowed + ". Lösung: eine erlaubte Kategorie "
                "verwenden oder Format 'smart' (freie Kategorien) wählen."
            )

    # -- Versions-Heading (formatabhängig) --------------------------------
    def version_heading(self, version: str, date: str) -> str:
        """Return the version heading line for a version/date pair."""
        raise NotImplementedError

    def _v(self, version: str) -> str:
        """Version mit konfiguriertem Anzeige-Prefix."""
        return self.prefix + version

    # -- Header -----------------------------------------------------------
    def format_initial_changelog(self) -> str:
        """Return the header block for a fresh changelog file."""
        return "# Changelog\n"

    # -- Einzeleintrag (CHANGELOG-full.md) --------------------------------
    def format_entry(self, entry: EntryRecord) -> str:
        """Render a single entry with its details for the full changelog."""
        lines = [self.version_heading(entry.version, entry.date), ""]
        lines.append("### " + entry.category)
        lines.append("- " + entry.description)
        for detail in entry.details:
            lines.append("  - " + detail)
        if entry.files:
            lines.append("  - Dateien: " + ", ".join(entry.files))
        return "\n".join(lines)

    # -- Kuratierter Release-Block (CHANGELOG.md) -------------------------
    def format_release(self, release: ReleaseRecord) -> str:
        """Render a curated release block grouped by category."""
        lines = [self.version_heading(release.version, release.date), ""]
        for section in release.summary:
            lines.append("### " + section.category)
            for item in section.items:
                lines.append("- " + item)
            lines.append("")
        # Letzte Leerzeile entfernen (Spacing macht der Renderer).
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)
