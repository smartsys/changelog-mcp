"""Record-Modelle des Stores (Discriminated Union über 'type').

SemVer-Pattern ^\\d+\\.\\d+\\.\\d+$. Die JSONL-Felder sind fest (byte-stabil).
Optionale Felder details/files werden immer als Liste geschrieben.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"


class Section(BaseModel):
    """A curated group of release notes for one category."""

    model_config = ConfigDict(extra="forbid")

    category: str
    items: list[str] = Field(min_length=1)


class EntryRecord(BaseModel):
    """A single recorded change (append-only, referenced by releases)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["entry"] = "entry"
    id: str
    version: str = Field(pattern=SEMVER_PATTERN)
    date: str
    ts: str
    category: str
    description: str
    details: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    # Privater Eintrag: wird standardmäßig weder in CHANGELOG.md noch in
    # CHANGELOG-full.md publiziert (siehe includePrivate-Flags der Config).
    private: bool = False


class ReleaseRecord(BaseModel):
    """A curated release bundling a span of entries."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: Literal["release"] = "release"
    version: str = Field(pattern=SEMVER_PATTERN)
    date: str
    ts: str
    # Leer erlaubt: ein Release nur aus privaten Einträgen hat keinen
    # öffentlichen Block (siehe create_release / render_public).
    summary: list[Section] = Field(default_factory=list)
    entry_ids: list[str] = Field(default_factory=list, alias="entryIds")


class EditRecord(BaseModel):
    """A correction that supersedes fields of an earlier entry (append-only).

    Referenziert die Ziel-Entry-ID. Nur gesetzte Felder überschreiben; None
    lässt das jeweilige Feld unverändert. Der Read-Layer löst Edits auf.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["edit"] = "edit"
    id: str
    ts: str
    category: str | None = None
    description: str | None = None
    details: list[str] | None = None
    files: list[str] | None = None


class DeleteRecord(BaseModel):
    """A tombstone that removes an earlier entry from the effective view."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["delete"] = "delete"
    id: str
    ts: str


# Discriminated Union: Unterscheidung über das Feld 'type'.
Record = Annotated[
    EntryRecord | ReleaseRecord | EditRecord | DeleteRecord,
    Field(discriminator="type"),
]


def record_to_line(
    record: EntryRecord | ReleaseRecord | EditRecord | DeleteRecord
) -> str:
    """Serialize a record to a compact, byte-stable JSONL line (no trailing NL).

    Uses camelCase aliases and compact separators; ensure_ascii=False keeps
    umlauts readable. json.dumps escapes newlines, so a record is always one line.
    """
    import json

    data = record.model_dump(by_alias=True)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
