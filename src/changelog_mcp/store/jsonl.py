"""Append-only JSONL-I/O mit Zeilen-Validierung.

Ein abgebrochener Schreibvorgang beschädigt höchstens die letzte Zeile. Sie wird
beim Lesen per Schema erkannt, gemeldet und übersprungen. Fehlender Store = leer.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from ..utils.files import atomic_append, read_text_lines
from .models import (
    DeleteRecord,
    EditRecord,
    EntryRecord,
    Record,
    ReleaseRecord,
    record_to_line,
)

_RECORD_ADAPTER: TypeAdapter[Record] = TypeAdapter(Record)

# Aufgelöste Sicht: nur Entries und Releases (Edits/Tilgungen sind eingerechnet).
AnyRecord = EntryRecord | ReleaseRecord
# Schreibbare Record-Typen (inkl. Korrektur- und Tilgungs-Records).
WritableRecord = EntryRecord | ReleaseRecord | EditRecord | DeleteRecord


class ReadResult:
    """Records read from the store plus warnings about skipped corrupt lines."""

    def __init__(self, records: list[AnyRecord], warnings: list[str]) -> None:
        self.records = records
        self.warnings = warnings


def _resolve_corrections(raw: list[WritableRecord]) -> list[AnyRecord]:
    """Fold edit/delete records into the entries they target.

    Getilgte Entries entfallen; Edits überschreiben die gesetzten Felder
    (spätere Edits gewinnen). Releases bleiben unverändert. Store-Reihenfolge
    bleibt erhalten.
    """
    edits: dict[str, dict[str, object]] = {}
    deleted: set[str] = set()
    for record in raw:
        if isinstance(record, DeleteRecord):
            deleted.add(record.id)
        elif isinstance(record, EditRecord):
            changes = {
                key: value
                for key, value in {
                    "category": record.category,
                    "description": record.description,
                    "details": record.details,
                    "files": record.files,
                }.items()
                if value is not None
            }
            edits.setdefault(record.id, {}).update(changes)

    resolved: list[AnyRecord] = []
    for record in raw:
        if isinstance(record, EntryRecord):
            if record.id in deleted:
                continue
            if record.id in edits:
                record = record.model_copy(update=edits[record.id])
            resolved.append(record)
        elif isinstance(record, ReleaseRecord):
            resolved.append(record)
    return resolved


def read_store(path: Path, encoding: str = "utf-8") -> ReadResult:
    """Read all valid records, resolved. Corrupt lines are skipped and reported.

    Edit-/Delete-Records werden eingerechnet, sodass Aufrufer die effektive
    Sicht (Entries + Releases) erhalten. A missing store file yields an empty
    result (kein Fehler).
    """
    raw: list[WritableRecord] = []
    warnings: list[str] = []
    lines = read_text_lines(path, encoding=encoding)
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            data = json.loads(stripped)
            record = _RECORD_ADAPTER.validate_python(data)
        except (json.JSONDecodeError, ValidationError):
            warnings.append(
                "Zeile " + str(number) + " im Store ist defekt und wurde "
                "übersprungen. Lösung: Zeile prüfen; die übrigen Records "
                "bleiben nutzbar."
            )
            continue
        raw.append(record)
    return ReadResult(_resolve_corrections(raw), warnings)


def append_records(
    path: Path, records: list[WritableRecord], encoding: str = "utf-8"
) -> None:
    """Append all *records* in a single atomic O_APPEND write."""
    if not records:
        return
    payload = "".join(record_to_line(rec) + "\n" for rec in records)
    atomic_append(path, payload, encoding=encoding)
