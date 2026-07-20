"""Abgeleiteter Zustand: Unreleased, höchste Version, Suche mit Ranking.

Nie gespeichert, immer frisch aus den Records berechnet.
"""

from __future__ import annotations

from ..parser.version import FALLBACK_VERSION, parse_version
from .jsonl import AnyRecord
from .models import EntryRecord, ReleaseRecord

# Ranking-Gewichte für die Volltextsuche.
RANK_DESCRIPTION = 10
RANK_DETAILS = 4
RANK_FILES = 2
RANK_CATEGORY = 1


def entries(records: list[AnyRecord]) -> list[EntryRecord]:
    """Return only entry records, preserving store order."""
    return [r for r in records if isinstance(r, EntryRecord)]


def releases(records: list[AnyRecord]) -> list[ReleaseRecord]:
    """Return only release records, preserving store order."""
    return [r for r in records if isinstance(r, ReleaseRecord)]


def released_entry_ids(records: list[AnyRecord]) -> set[str]:
    """Return the set of entry ids referenced by any release."""
    ids: set[str] = set()
    for rel in releases(records):
        ids.update(rel.entry_ids)
    return ids


def unreleased_entries(records: list[AnyRecord]) -> list[EntryRecord]:
    """Return entries whose id is not referenced by any release."""
    released = released_entry_ids(records)
    return [e for e in entries(records) if e.id not in released]


def public_unreleased_entries(
    records: list[AnyRecord], include_private: bool
) -> list[EntryRecord]:
    """Unreleased entries visible for the curated changelog.

    With *include_private* False, private entries are hidden so they never
    reach the CHANGELOG.md summary the AI writes.
    """
    unreleased = unreleased_entries(records)
    if include_private:
        return unreleased
    return [e for e in unreleased if not e.private]


def has_any_version(records: list[AnyRecord]) -> bool:
    """True if the store contains at least one entry or release."""
    return any(isinstance(r, (EntryRecord, ReleaseRecord)) for r in records)


def highest_version(records: list[AnyRecord]) -> str:
    """Return the highest version across entries and releases (fallback 0.0.0)."""
    best: str | None = None
    for record in records:
        version = record.version
        if best is None or parse_version(version) > parse_version(best):
            best = version
    return best if best is not None else FALLBACK_VERSION


def next_release_version(records: list[AnyRecord]) -> str | None:
    """Highest version among the unreleased entries (the release would carry it)."""
    unreleased = unreleased_entries(records)
    if not unreleased:
        return None
    best = unreleased[0].version
    for entry in unreleased[1:]:
        if parse_version(entry.version) > parse_version(best):
            best = entry.version
    return best


def get_release(records: list[AnyRecord], version: str) -> ReleaseRecord | None:
    """Find a release by exact version string."""
    for rel in releases(records):
        if rel.version == version:
            return rel
    return None


def entries_for_release(
    records: list[AnyRecord], release: ReleaseRecord
) -> list[EntryRecord]:
    """Return the bundled entries of a release, sorted by version descending."""
    by_id = {e.id: e for e in entries(records)}
    bundled = [by_id[i] for i in release.entry_ids if i in by_id]
    bundled.sort(key=lambda e: parse_version(e.version), reverse=True)
    return bundled


def _score(entry: EntryRecord, query: str) -> int:
    """Relevance score of *entry* for a lowercase *query* substring."""
    score = 0
    if query in entry.description.lower():
        score += RANK_DESCRIPTION
    if any(query in d.lower() for d in entry.details):
        score += RANK_DETAILS
    if any(query in f.lower() for f in entry.files):
        score += RANK_FILES
    if query in entry.category.lower():
        score += RANK_CATEGORY
    return score


def search_entries(
    records: list[AnyRecord],
    query: str | None = None,
    category: str | None = None,
    file: str | None = None,
    version: str | None = None,
    released: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
) -> list[EntryRecord]:
    """Search entries. All filters are optional and AND-combined.

    Full-text ranking: description(10) > details(4) > files(2) > category(1).
    Without a query, results are sorted by version descending.
    """
    released_ids = released_entry_ids(records)
    candidates = entries(records)
    scored: list[tuple[int, EntryRecord]] = []

    for entry in candidates:
        # Kategorie: case-insensitive exakt.
        if category is not None and entry.category.lower() != category.lower():
            continue
        # Datei: Teilstring über alle files.
        if file is not None and not any(file in f for f in entry.files):
            continue
        # Version: Präfix-Vergleich.
        if version is not None and not entry.version.startswith(version):
            continue
        # Release-Status.
        if released is not None:
            is_released = entry.id in released_ids
            if is_released != released:
                continue
        # Datumsbereich (inklusive, lexikografisch auf ISO-ähnlichen Strings).
        if date_from is not None and entry.date < date_from:
            continue
        if date_to is not None and entry.date > date_to:
            continue
        # Volltext-Ranking.
        if query:
            score = _score(entry, query.lower())
            if score == 0:
                continue
            scored.append((score, entry))
        else:
            scored.append((0, entry))

    if query:
        scored.sort(
            key=lambda pair: (pair[0], parse_version(pair[1].version)), reverse=True
        )
    else:
        scored.sort(key=lambda pair: parse_version(pair[1].version), reverse=True)

    return [entry for _, entry in scored[:limit]]
