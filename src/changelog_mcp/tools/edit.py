"""Tools edit_entry / delete_entry: einen Eintrag per ID ändern oder löschen.

Append-only-konform: Änderung und Löschung werden als Korrektur- bzw.
Tilgungs-Record angehängt. Der Read-Layer (store.jsonl) rechnet sie ein, sodass
der Eintrag danach in allen Ausgaben geändert bzw. entfernt erscheint. Bestehende
Zeilen werden nie mutiert; der Store bleibt jederzeit reproduzierbar.
"""

from __future__ import annotations

from pathlib import Path

from ..store.jsonl import AnyRecord
from ..store.models import DeleteRecord, EditRecord, EntryRecord
from ..store.query import entries, released_entry_ids
from ..utils.date import now_ts
from .support import build_env, rerender_full, warnings_suffix, write_records


def _find_entry(records: list[AnyRecord], entry_id: str) -> EntryRecord | None:
    """Return the effective entry with *entry_id*, or None if absent."""
    for entry in entries(records):
        if entry.id == entry_id:
            return entry
    return None


def _not_found_error(entry_id: str) -> str:
    """Deutsche Fehlermeldung für eine unbekannte Entry-ID."""
    return (
        "Eintrag nicht gefunden. Kontext: keine Entry-ID '" + entry_id
        + "' im Store. Lösung: search_entries oder list_unreleased nutzen, um "
        "die korrekte ID zu ermitteln."
    )


def edit_entry(
    id: str,
    category: str | None = None,
    description: str | None = None,
    details: list[str] | None = None,
    files: list[str] | None = None,
    cwd: Path | None = None,
) -> str:
    """Change fields of an existing entry by id (append-only correction).

    Nur übergebene Felder werden geändert; nicht genannte bleiben unverändert.
    Version und Datum des Eintrags bleiben erhalten. Die Markdown-Dateien werden
    nicht geschrieben — render_changelog oder create_release erledigt das.
    """
    env = build_env(cwd)
    entry = _find_entry(env.records, id)
    if entry is None:
        return _not_found_error(id)

    changed: list[str] = []
    if category is not None:
        env.formatter.validate_category(category)
        changed.append("Kategorie")
    if description is not None:
        if not description.strip():
            return (
                "Leere Beschreibung. Kontext: edit_entry für '" + id + "'. "
                "Lösung: einen nicht-leeren Text angeben."
            )
        changed.append("Beschreibung")
    if details is not None:
        changed.append("Details")
    if files is not None:
        changed.append("Dateien")

    if not changed:
        return (
            "Keine Änderung angegeben. Kontext: edit_entry für '" + id + "'. "
            "Lösung: mindestens eines von category, description, details, files "
            "übergeben."
        )

    correction = EditRecord(
        id=id,
        ts=now_ts(),
        category=category,
        description=description,
        details=details,
        files=files,
    )
    write_records(env, [correction])
    # Detail-Changelog sofort neu erzeugen, damit CHANGELOG-full.md aktuell bleibt.
    rerender_full(cwd)

    is_released = id in released_entry_ids(env.records)
    hint = (
        " CHANGELOG-full.md aktualisiert. Der Eintrag ist bereits Teil eines"
        " Releases; die kuratierte CHANGELOG.md aktualisiert create_release oder"
        " render_changelog."
        if is_released
        else " CHANGELOG-full.md aktualisiert."
    )
    return (
        "Eintrag " + id + " geändert. Felder: " + ", ".join(changed) + "."
        + hint + warnings_suffix(env.warnings)
    )


def delete_entry(id: str, cwd: Path | None = None) -> str:
    """Delete an entry by id (append-only tombstone).

    Nur unveröffentlichte Einträge sind löschbar; bereits released Einträge sind
    publizierte Historie und bleiben erhalten.
    """
    env = build_env(cwd)
    entry = _find_entry(env.records, id)
    if entry is None:
        return _not_found_error(id)

    if id in released_entry_ids(env.records):
        return (
            "Löschen abgelehnt. Kontext: Eintrag '" + id + "' ist bereits Teil "
            "eines Releases (publizierte Historie). Lösung: statt Löschen einen "
            "korrigierenden Eintrag über add_entry ergänzen."
        )

    tombstone = DeleteRecord(id=id, ts=now_ts())
    write_records(env, [tombstone])
    # Detail-Changelog sofort neu erzeugen, damit CHANGELOG-full.md aktuell bleibt.
    rerender_full(cwd)

    return (
        "Eintrag " + id + " gelöscht. Er entfällt in allen Ausgaben; "
        "CHANGELOG-full.md aktualisiert."
        + warnings_suffix(env.warnings)
    )
