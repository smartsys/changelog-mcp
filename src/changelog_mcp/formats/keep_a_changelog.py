"""Format 'keep-a-changelog' (strikte Kategorien)."""

from __future__ import annotations

from .base import ChangelogFormatter


class KeepAChangelogFormatter(ChangelogFormatter):
    """Keep a Changelog preset: ## [X.Y.Z] - YYYY-MM-DD."""

    name = "keep-a-changelog"
    categories = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
    strict = True

    def version_heading(self, version: str, date: str) -> str:
        return "## [" + self._v(version) + "] - " + date

    def format_initial_changelog(self) -> str:
        return (
            "# Changelog\n\n"
            "Alle nennenswerten Änderungen an diesem Projekt werden hier "
            "dokumentiert.\n\n"
            "Das Format basiert auf [Keep a Changelog]"
            "(https://keepachangelog.com/de/1.1.0/).\n"
        )
