"""Migration: import_records (idempotent) und verify_store."""

from __future__ import annotations

from pathlib import Path

from changelog_mcp.tools.import_ import (
    ImportEntrySchema,
    ImportReleaseSchema,
    import_records,
    verify_store,
)
from changelog_mcp.tools.init import init_changelog


def _entry(version: str) -> ImportEntrySchema:
    return ImportEntrySchema(
        version=version,
        date="2026-07-13",
        category="Added",
        description="Import " + version,
    )


def test_import_skips_existing_versions(project: Path) -> None:
    init_changelog(cwd=project)
    import_records([_entry("0.1.0"), _entry("0.1.1")], cwd=project)
    # Wiederholung: beide Versionen bereits vorhanden -> übersprungen.
    msg = import_records(
        [_entry("0.1.0"), _entry("0.1.1"), _entry("0.1.2")], cwd=project
    )
    assert "importiert: 1" in msg
    assert "übersprungen (bereits vorhanden): 2" in msg


def test_import_release_resolves_entry_versions(project: Path) -> None:
    init_changelog(cwd=project)
    releases = [
        ImportReleaseSchema(
            version="0.1.1",
            date="2026-07-13",
            summary=[{"category": "Added", "items": ["Erstes Release"]}],
            entryVersions=["0.1.0", "0.1.1"],
        )
    ]
    msg = import_records(
        [_entry("0.1.0"), _entry("0.1.1")], releases=releases, cwd=project
    )
    assert "Releases importiert: 1" in msg


def test_verify_store_reports_missing(project: Path) -> None:
    init_changelog(cwd=project)
    import_records([_entry("0.1.0")], cwd=project)
    source = project / "OLD-CHANGELOG.md"
    source.write_text(
        "## [0.1.0] - 2026-07-13\n## [0.2.0] - 2026-07-14\n", encoding="utf-8"
    )

    msg = verify_store("OLD-CHANGELOG.md", cwd=project)
    assert "fehlgeschlagen" in msg
    assert "0.2.0" in msg


def test_verify_store_success(project: Path) -> None:
    init_changelog(cwd=project)
    import_records([_entry("0.1.0")], cwd=project)
    source = project / "OLD.md"
    source.write_text("## [0.1.0] - 2026-07-13\n", encoding="utf-8")
    msg = verify_store("OLD.md", cwd=project)
    assert "erfolgreich" in msg
