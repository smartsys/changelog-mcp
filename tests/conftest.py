"""Gemeinsame Test-Fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from changelog_mcp.store.models import EntryRecord, ReleaseRecord, Section


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Isoliertes Projektverzeichnis (Zero-Config, kein Git-Repo)."""
    return tmp_path


def make_entry(
    entry_id: str,
    version: str,
    category: str = "Added",
    description: str = "Etwas",
    details: list[str] | None = None,
    files: list[str] | None = None,
    date: str = "2026-07-13",
    private: bool = False,
) -> EntryRecord:
    """Factory für einen EntryRecord (keine hartkodierten Testdaten in Tests)."""
    return EntryRecord(
        id=entry_id,
        version=version,
        date=date,
        ts="2026-07-13T10:00:00.000Z",
        category=category,
        description=description,
        details=details or [],
        files=files or [],
        private=private,
    )


def make_release(
    version: str,
    entry_ids: list[str],
    category: str = "Added",
    items: list[str] | None = None,
    date: str = "2026-07-13",
) -> ReleaseRecord:
    """Factory für einen ReleaseRecord."""
    return ReleaseRecord(
        version=version,
        date=date,
        ts="2026-07-13T11:00:00.000Z",
        summary=[Section(category=category, items=items or ["Zusammenfassung"])],
        entry_ids=entry_ids,
    )
