"""Tools list_unreleased, preview_release, create_release."""

from __future__ import annotations

from pathlib import Path

from ..formats.base import ChangelogFormatter
from ..render.markdown import render_all
from ..store.models import ReleaseRecord, Section
from ..store.query import (
    highest_version,
    next_release_version,
    public_unreleased_entries,
    unreleased_entries,
)
from ..utils.date import now_ts, today_str
from .support import build_env, warnings_suffix, write_records


def _validate_sections(
    formatter: ChangelogFormatter, summary: list[Section]
) -> None:
    """Validate every section category against the active format."""
    for section in summary:
        formatter.validate_category(section.category)


def list_unreleased(cwd: Path | None = None) -> str:
    """List all entries since the last release and the version a release would carry.

    Private Einträge werden ausgeblendet, solange changelog.includePrivate=false —
    so gelangen sie nicht in den kuratierten Summary, den die KI daraus schreibt.
    """
    env = build_env(cwd)
    include_private = env.result.config.changelog.include_private
    visible = public_unreleased_entries(env.records, include_private)
    hidden = len(unreleased_entries(env.records)) - len(visible)

    if not visible:
        if hidden:
            return (
                "Keine öffentlichen unveröffentlichten Einträge (" + str(hidden)
                + " privat ausgeblendet). Ein Release würde nur private Einträge "
                "bündeln; CHANGELOG.md bekommt keinen neuen Block."
                + warnings_suffix(env.warnings)
            )
        return "Keine unveröffentlichten Einträge." + warnings_suffix(env.warnings)

    version = next_release_version(env.records)
    lines = [
        "Unveröffentlichte Einträge (" + str(len(visible)) + "), Release würde "
        "Version " + str(version) + " tragen:",
    ]
    for entry in visible:
        lines.append(
            "- " + entry.id + " | " + entry.version + " [" + entry.category + "] "
            + entry.description
        )
    if hidden:
        lines.append(
            "(" + str(hidden) + " private Einträge ausgeblendet — nicht in den "
            "Summary aufnehmen.)"
        )
    return "\n".join(lines) + warnings_suffix(env.warnings)


def preview_release(summary: list[Section], cwd: Path | None = None) -> str:
    """Render the release block exactly like create_release, without writing."""
    env = build_env(cwd)
    _validate_sections(env.formatter, summary)
    version = next_release_version(env.records) or highest_version(env.records)
    preview = ReleaseRecord(
        version=version,
        date=today_str(env.result.config.date_format),
        ts=now_ts(),
        summary=summary,
        entry_ids=[],
    )
    block = env.formatter.format_release(preview)
    return "Vorschau Release " + version + ":\n\n" + block + warnings_suffix(
        env.warnings
    )


def create_release(
    summary: list[Section] | None = None, cwd: Path | None = None
) -> str:
    """Bundle all unreleased entries into a release and re-render both markdown files.

    Es werden immer *alle* offenen Einträge gebündelt (auch private), damit sie als
    released gelten und CHANGELOG-full.md sie zeigen kann. Der *summary* beschreibt
    nur den öffentlichen Block. Gibt es keine öffentlichen Einträge (alle privat und
    includePrivate=false), ist ein leerer summary zulässig — dann entsteht kein
    öffentlicher CHANGELOG.md-Block.
    """
    env = build_env(cwd)
    config = env.result.config
    unreleased = unreleased_entries(env.records)
    if not unreleased:
        return (
            "Nichts unveröffentlicht — kein Release erstellt. Kontext: es gibt "
            "keine Einträge seit dem letzten Release. Lösung: zuerst add_entry "
            "ausführen." + warnings_suffix(env.warnings)
        )

    summary = summary or []
    has_public = bool(
        public_unreleased_entries(env.records, config.changelog.include_private)
    )
    # Öffentliche Einträge ohne Summary wären ein Versehen (leerer Block).
    if has_public and not summary:
        return (
            "Summary fehlt — kein Release erstellt. Kontext: es gibt öffentliche "
            "unveröffentlichte Einträge, aber keine kuratierten Abschnitte. Lösung: "
            "list_unreleased ausführen und die Einträge zu Sections verdichten."
            + warnings_suffix(env.warnings)
        )
    _validate_sections(env.formatter, summary)

    # unreleased ist oben als nicht-leer geprüft, der Fallback greift nie —
    # er hält den Typ str (gleiche Form wie in preview_release).
    version = next_release_version(env.records) or highest_version(env.records)
    release = ReleaseRecord(
        version=version,
        date=today_str(config.date_format),
        ts=now_ts(),
        summary=summary,
        entry_ids=[e.id for e in unreleased],
    )
    write_records(env, [release])

    # Nach dem Anhängen frisch lesen und beide Markdown-Dateien neu rendern.
    fresh = build_env(cwd)
    outcome = render_all(fresh.result, fresh.records, fresh.formatter)

    parts = [
        "Release " + version + " erstellt (" + str(len(unreleased)) + " Einträge "
        "gebündelt).",
    ]
    parts.append(
        "CHANGELOG.md: " + ("geschrieben" if outcome.public_written else "übersprungen")
        + ", CHANGELOG-full.md: "
        + ("geschrieben" if outcome.full_written else "deaktiviert") + "."
    )
    return " ".join(parts) + warnings_suffix(env.warnings)
