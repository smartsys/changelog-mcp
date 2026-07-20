"""Tool add_entry: einen Einzeleintrag anhängen (append-only)."""

from __future__ import annotations

from pathlib import Path

from ..parser.version import initial_version, next_version
from ..store.models import EntryRecord
from ..store.query import has_any_version, highest_version, unreleased_entries
from ..utils.date import now_ts, today_str
from .support import (
    build_env,
    new_entry_id,
    rerender_full,
    warnings_suffix,
    write_records,
)


def add_entry(
    category: str,
    description: str,
    details: list[str] | None = None,
    files: list[str] | None = None,
    bump: str = "patch",
    private: bool = False,
    cwd: Path | None = None,
) -> str:
    """Validate the category, compute the next version and append one entry.

    Does not touch the markdown files. Returns version + unreleased count.
    A private entry stays out of the published changelogs unless the matching
    includePrivate flag is set.
    """
    env = build_env(cwd)
    config = env.result.config
    # Kategorie gegen das aktive Format validieren (strikt bei keep/conventional).
    env.formatter.validate_category(category)

    versioning = config.versioning
    if has_any_version(env.records):
        version = next_version(
            highest_version(env.records),
            bump,
            versioning.mode,
            versioning.fixed_major,
            versioning.fixed_minor,
        )
    else:
        version = initial_version(versioning.fixed_major, versioning.fixed_minor)

    entry = EntryRecord(
        id=new_entry_id(),
        version=version,
        date=today_str(config.date_format),
        ts=now_ts(),
        category=category,
        description=description,
        details=details or [],
        files=files or [],
        private=private,
    )
    write_records(env, [entry])
    # Detail-Changelog sofort neu erzeugen, damit CHANGELOG-full.md aktuell bleibt.
    full_written = rerender_full(cwd)

    unreleased_count = len(unreleased_entries(env.records)) + 1
    private_note = " (privat)" if private else ""
    full_note = (
        " CHANGELOG-full.md aktualisiert." if full_written else ""
    )
    return (
        "Eintrag hinzugefügt" + private_note + ". Version: " + version
        + ". Kategorie: " + category
        + ". Unveröffentlichte Einträge: " + str(unreleased_count)
        + "." + full_note + warnings_suffix(env.warnings)
    )
