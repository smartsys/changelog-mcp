"""Tools search_entries und get_release."""

from __future__ import annotations

from pathlib import Path

from ..store.query import entries_for_release
from ..store.query import get_release as find_release
from ..store.query import search_entries as run_search
from .support import build_env, warnings_suffix


def search_entries(
    query: str | None = None,
    category: str | None = None,
    file: str | None = None,
    version: str | None = None,
    released: bool | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    limit: int = 10,
    cwd: Path | None = None,
) -> str:
    """Search the structured store. All filters optional and AND-combined."""
    env = build_env(cwd)
    results = run_search(
        env.records,
        query=query,
        category=category,
        file=file,
        version=version,
        released=released,
        date_from=dateFrom,
        date_to=dateTo,
        limit=limit,
    )
    if not results:
        return "Keine Treffer." + warnings_suffix(env.warnings)

    lines = [str(len(results)) + " Treffer:"]
    for entry in results:
        line = "- " + entry.id + " | " + entry.version + " (" + entry.date + ") ["
        line += entry.category + "] " + entry.description
        if entry.files:
            line += " — " + ", ".join(entry.files)
        lines.append(line)
    return "\n".join(lines) + warnings_suffix(env.warnings)


def get_release(version: str, cwd: Path | None = None) -> str:
    """Show a release with its curated summary and all bundled entries."""
    env = build_env(cwd)
    release = find_release(env.records, version)
    if release is None:
        return (
            "Release '" + version + "' nicht gefunden. Kontext: keine passende "
            "Release-Version im Store. Lösung: get_current_version nutzen oder "
            "search_entries für vorhandene Versionen."
            + warnings_suffix(env.warnings)
        )

    lines = [
        "Release " + release.version + " (" + release.date + "):",
        "",
        "Zusammenfassung:",
    ]
    for section in release.summary:
        lines.append("  " + section.category + ":")
        for item in section.items:
            lines.append("    - " + item)

    bundled = entries_for_release(env.records, release)
    lines.append("")
    lines.append("Gebündelte Einträge (" + str(len(bundled)) + "):")
    for entry in bundled:
        lines.append(
            "  - " + entry.version + " [" + entry.category + "] " + entry.description
        )
    return "\n".join(lines) + warnings_suffix(env.warnings)
