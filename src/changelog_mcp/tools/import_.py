"""Tools import_records und verify_store (Migration)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..parser.changelog import extract_versions
from ..store.jsonl import WritableRecord
from ..store.models import SEMVER_PATTERN, EntryRecord, ReleaseRecord, Section
from ..store.query import entries as store_entries
from ..store.query import releases as store_releases
from ..utils.date import now_ts
from ..utils.files import read_text
from ..utils.security import resolve_source_file
from .support import build_env, new_entry_id, write_records


class ImportEntrySchema(BaseModel):
    """A parsed entry supplied by the AI for migration."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(pattern=SEMVER_PATTERN)
    date: str
    category: str
    description: str
    details: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    private: bool = False


class ImportReleaseSchema(BaseModel):
    """A parsed release supplied by the AI for migration."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    version: str = Field(pattern=SEMVER_PATTERN)
    date: str
    summary: list[Section] = Field(min_length=1)
    entry_versions: list[str] = Field(default_factory=list, alias="entryVersions")


def import_records(
    entries: list[ImportEntrySchema],
    releases: list[ImportReleaseSchema] | None = None,
    cwd: Path | None = None,
) -> str:
    """Append parsed entries (and optional releases) to the store.

    Entries whose version already exists are skipped -> a broken import is
    repeatable. Releases reference entries by version (resolved to ids).
    """
    env = build_env(cwd)
    existing_entry_versions = {e.version for e in store_entries(env.records)}
    existing_release_versions = {r.version for r in store_releases(env.records)}

    # Version -> id-Map über bestehende Store-Einträge.
    version_to_id: dict[str, str] = {
        e.version: e.id for e in store_entries(env.records)
    }

    new_records: list[WritableRecord] = []
    imported = 0
    skipped = 0
    for item in entries:
        if item.version in existing_entry_versions:
            skipped += 1
            continue
        entry = EntryRecord(
            id=new_entry_id(),
            version=item.version,
            date=item.date,
            ts=now_ts(),
            category=item.category,
            description=item.description,
            details=item.details,
            files=item.files,
            private=item.private,
        )
        new_records.append(entry)
        # Map aktualisieren, damit Releases neue Einträge referenzieren können.
        version_to_id[item.version] = entry.id
        existing_entry_versions.add(item.version)
        imported += 1

    imported_releases = 0
    skipped_releases = 0
    for rel in releases or []:
        if rel.version in existing_release_versions:
            skipped_releases += 1
            continue
        entry_ids = [
            version_to_id[v] for v in rel.entry_versions if v in version_to_id
        ]
        release_record = ReleaseRecord(
            version=rel.version,
            date=rel.date,
            ts=now_ts(),
            summary=rel.summary,
            entry_ids=entry_ids,
        )
        new_records.append(release_record)
        existing_release_versions.add(rel.version)
        imported_releases += 1

    if new_records:
        write_records(env, new_records)

    return (
        "Import abgeschlossen. Einträge importiert: " + str(imported)
        + ", übersprungen (bereits vorhanden): " + str(skipped)
        + ". Releases importiert: " + str(imported_releases)
        + ", übersprungen: " + str(skipped_releases) + "."
    )


def verify_store(sourceFile: str, cwd: Path | None = None) -> str:
    """Compare version headings of *sourceFile* with the store and report gaps.

    Sicherheitsnetz der Migration: muss erfolgreich sein, bevor render_changelog
    läuft, sonst überschreibt das Rendering die Quelldatei mit unvollständigem Stand.
    """
    env = build_env(cwd)
    source_path = resolve_source_file(env.result.root, sourceFile)
    if not source_path.exists():
        return (
            "Quelldatei nicht gefunden: '" + str(source_path) + "'. Lösung: "
            "relativen Pfad zur bestehenden Changelog-Datei angeben."
        )

    text = read_text(source_path)
    source_versions = extract_versions(text)
    store_versions = {r.version for r in env.records}
    missing = [v for v in source_versions if v not in store_versions]

    if missing:
        return (
            "Verifikation fehlgeschlagen: " + str(len(missing)) + " Version(en) "
            "aus '" + sourceFile + "' fehlen im Store: " + ", ".join(missing)
            + ". Lösung: fehlende Einträge per import_records nachtragen, dann "
            "erneut verify_store. render_changelog erst nach erfolgreicher Prüfung."
        )

    return (
        "Verifikation erfolgreich: alle " + str(len(source_versions)) + " Version(en) "
        "aus '" + sourceFile + "' sind im Store vorhanden. render_changelog ist "
        "jetzt sicher."
    )
