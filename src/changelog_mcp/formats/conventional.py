"""Format 'conventional' (strikte Kategorien)."""

from __future__ import annotations

from .base import ChangelogFormatter


class ConventionalFormatter(ChangelogFormatter):
    """Conventional Commits preset: ## X.Y.Z (YYYY-MM-DD)."""

    name = "conventional"
    categories = (
        "Features",
        "Bug Fixes",
        "Performance",
        "Reverts",
        "Breaking Changes",
    )
    strict = True

    def version_heading(self, version: str, date: str) -> str:
        return "## " + self._v(version) + " (" + date + ")"

    def format_initial_changelog(self) -> str:
        return "# Changelog\n"
