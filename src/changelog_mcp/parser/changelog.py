"""Markdown-Heading-Erkennung — ausschließlich für verify_store.

Erkennt Versions-Headings aller drei Formate über Regex und extrahiert die
SemVer-Nummern. Das inhaltliche Parsen bestehender Changelogs übernimmt die KI.
"""

from __future__ import annotations

import re

# Erfasst Versions-Headings der drei Formate:
#   keep-a-changelog: ## [1.2.3] - 2026-07-13
#   conventional:     ## 1.2.3 (2026-07-13)
#   smart:            ## [1.2.3] - 2026-07-13
# Wir suchen Zeilen, die wie ein Heading beginnen, und ziehen die erste SemVer.
_HEADING_LINE = re.compile(r"^\s*(#{1,6}\s*|v)", re.IGNORECASE)
_SEMVER = re.compile(r"(\d+\.\d+\.\d+)")


def extract_versions(text: str) -> list[str]:
    """Return the ordered, de-duplicated list of versions found in *text*."""
    seen: dict[str, None] = {}
    for line in text.splitlines():
        if not _HEADING_LINE.match(line):
            continue
        match = _SEMVER.search(line)
        if match:
            seen.setdefault(match.group(1), None)
    return list(seen.keys())
