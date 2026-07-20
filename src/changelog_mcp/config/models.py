"""Pydantic-Modelle der Konfiguration (siehe README, Abschnitt „Konfiguration").

JSON-Schlüssel sind camelCase (byte-stabil), Python-Attribute snake_case über
Aliase. Serialisierung erfolgt immer mit by_alias=True.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Encoding = Literal["utf-8", "utf-16le", "latin1", "ascii"]
VersioningMode = Literal["semver", "patch-only"]
FormatName = Literal["keep-a-changelog", "conventional", "smart"]
BackupInterval = Literal["daily", "weekly", "monthly"]


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class StoreConfig(_Base):
    """Location of the append-only JSONL store."""

    file: str = "changelog.jsonl"
    # Kanonisches Layout: Store, Detail-Changelog und Backups liegen gebündelt
    # unter documentation/changelog. Der Ordner wird bei Bedarf angelegt.
    path: str = "./documentation/changelog"


class ChangelogConfig(_Base):
    """Public curated changelog (CHANGELOG.md)."""

    file: str = "CHANGELOG.md"
    path: str = "./"
    encoding: Encoding = "utf-8"
    entry_spacing: int = Field(default=2, ge=0, alias="entrySpacing")
    # true: private Einträge fließen in den kuratierten CHANGELOG.md-Summary ein
    # (list_unreleased zeigt sie dann). false (Default): privat bleibt
    # öffentlich unsichtbar.
    include_private: bool = Field(default=False, alias="includePrivate")


class FullChangelogConfig(_Base):
    """Detailed changelog with every single entry (CHANGELOG-full.md)."""

    enabled: bool = True
    file: str = "CHANGELOG-full.md"
    # Beim Store gebündelt (siehe StoreConfig); die öffentliche CHANGELOG.md
    # bleibt bewusst im Projekt-Root.
    path: str = "./documentation/changelog"
    # true: private Einträge werden auch in CHANGELOG-full.md gerendert.
    include_private: bool = Field(default=False, alias="includePrivate")


class VersioningConfig(_Base):
    """Versioning strategy and display prefix."""

    mode: VersioningMode = "semver"
    prefix: str = ""
    fixed_major: int | None = Field(default=None, alias="fixedMajor")
    fixed_minor: int | None = Field(default=None, alias="fixedMinor")


class BackupConfig(_Base):
    """Rotierende Sicherung des Stores vor der ersten Änderung je Zeitraum."""

    enabled: bool = True
    path: str = "./documentation/changelog/backup"
    interval: BackupInterval = "daily"
    # Aufbewahrung: die neuesten N Backup-Dateien behalten, ältere entfernen.
    retention: int = Field(default=30, ge=1)
    # Dateiname-Muster; der Token {date} wird durch die Zeitraum-Kennung ersetzt.
    file_format: str = Field(default="changelog-{date}.jsonl", alias="fileFormat")


class Config(_Base):
    """Fully resolved changelog-mcp configuration."""

    format: FormatName = "smart"
    store: StoreConfig = Field(default_factory=StoreConfig)
    changelog: ChangelogConfig = Field(default_factory=ChangelogConfig)
    full_changelog: FullChangelogConfig = Field(
        default_factory=FullChangelogConfig, alias="fullChangelog"
    )
    versioning: VersioningConfig = Field(default_factory=VersioningConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    date_format: str = Field(default="YYYY-MM-DD", alias="dateFormat")
    language: str = "en"

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize with camelCase aliases (byte-stable representation)."""
        return self.model_dump(by_alias=True)
