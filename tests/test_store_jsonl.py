"""Store-Append/Read-Robustheit inkl. defekter letzter Zeile."""

from __future__ import annotations

from pathlib import Path

from changelog_mcp.store.jsonl import append_records, read_store

from .conftest import make_entry


def test_append_and_read_roundtrip(project: Path) -> None:
    store = project / "changelog.jsonl"
    e1 = make_entry("e-1", "0.1.0")
    e2 = make_entry("e-2", "0.1.1")
    append_records(store, [e1])
    append_records(store, [e2])

    result = read_store(store)
    assert [r.version for r in result.records] == ["0.1.0", "0.1.1"]
    assert result.warnings == []


def test_missing_store_is_empty(project: Path) -> None:
    result = read_store(project / "does-not-exist.jsonl")
    assert result.records == []
    assert result.warnings == []


def test_corrupt_last_line_is_skipped(project: Path) -> None:
    store = project / "changelog.jsonl"
    append_records(store, [make_entry("e-1", "0.1.0")])
    # Simuliert einen abgebrochenen Schreibvorgang: halbe letzte Zeile.
    with open(store, "a", encoding="utf-8") as handle:
        handle.write('{"type":"entry","id":"e-2","versi')

    result = read_store(store)
    assert [r.version for r in result.records] == ["0.1.0"]
    assert len(result.warnings) == 1
    assert "übersprungen" in result.warnings[0]


def test_single_atomic_append_for_multiple_records(project: Path) -> None:
    store = project / "changelog.jsonl"
    records = [make_entry(f"e-{i}", f"0.1.{i}") for i in range(3)]
    append_records(store, records)
    lines = store.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
