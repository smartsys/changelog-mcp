"""Rotierendes Store-Backup: Auslösung, Idempotenz, Rotation, Konfiguration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from changelog_mcp.config.loader import ConfigResult, load_config, store_path
from changelog_mcp.store.backup import ensure_backup
from changelog_mcp.store.jsonl import append_records
from changelog_mcp.tools.add import add_entry
from changelog_mcp.tools.init import init_changelog
from changelog_mcp.utils.security import SecurityError

from .conftest import make_entry


def _result(project: Path, **backup: object) -> ConfigResult:
    """ConfigResult mit optionalen backup-Overrides über eine Config-Datei."""
    if backup:
        (project / "changelog-mcp-config.json").write_text(
            json.dumps({"backup": backup}), encoding="utf-8"
        )
    return load_config(cwd=project)


def _fill_store(project: Path) -> Path:
    """Nicht-leeren Store anlegen und dessen Pfad zurückgeben."""
    result = load_config(cwd=project)
    store_file = store_path(result)
    append_records(store_file, [make_entry("e1", "0.1.0", description="Alpha")])
    return store_file


def _backup_dir(project: Path) -> Path:
    """Konfigurierten Backup-Ordner auflösen (unabhängig vom Default-Pfad)."""
    result = load_config(cwd=project)
    return result.root / result.config.backup.path


def _moment(day: int) -> datetime:
    return datetime(2026, 3, day, 10, 0, tzinfo=UTC)


def test_backup_wired_through_add(project: Path) -> None:
    # init legt leeren Store an -> erster add sichert nichts (leer),
    # zweiter add sichert den Stand nach dem ersten Eintrag.
    init_changelog(cwd=project)
    add_entry("Added", "Eintrag A", cwd=project)
    add_entry("Added", "Eintrag B", cwd=project)

    backups = list(_backup_dir(project).iterdir())
    assert len(backups) == 1
    content = backups[0].read_text(encoding="utf-8")
    assert "Eintrag A" in content
    assert "Eintrag B" not in content


def test_backup_skips_empty_store(project: Path) -> None:
    result = load_config(cwd=project)
    store_file = store_path(result)
    store_file.parent.mkdir(parents=True, exist_ok=True)
    store_file.write_text("", encoding="utf-8")
    assert ensure_backup(result, store_file, now=_moment(1)) is None
    assert not _backup_dir(project).exists()


def test_backup_idempotent_same_period(project: Path) -> None:
    store_file = _fill_store(project)
    result = load_config(cwd=project)
    first = ensure_backup(result, store_file, now=_moment(1))
    second = ensure_backup(result, store_file, now=_moment(1))
    assert first is not None
    assert second is None
    assert len(list(_backup_dir(project).iterdir())) == 1


def test_backup_disabled(project: Path) -> None:
    result = _result(project, enabled=False)
    store_file = store_path(result)
    append_records(store_file, [make_entry("e1", "0.1.0")])
    assert ensure_backup(result, store_file, now=_moment(1)) is None
    assert not _backup_dir(project).exists()


def test_rotation_keeps_latest_n(project: Path) -> None:
    result = _result(project, retention=3)
    store_file = store_path(result)
    append_records(store_file, [make_entry("e1", "0.1.0")])
    for day in (1, 2, 3, 4, 5):
        ensure_backup(result, store_file, now=_moment(day))

    names = sorted(p.name for p in _backup_dir(project).iterdir())
    assert names == [
        "changelog-2026-03-03.jsonl",
        "changelog-2026-03-04.jsonl",
        "changelog-2026-03-05.jsonl",
    ]


def test_interval_monthly_filename(project: Path) -> None:
    result = _result(project, interval="monthly")
    store_file = store_path(result)
    append_records(store_file, [make_entry("e1", "0.1.0")])
    ensure_backup(result, store_file, now=_moment(15))
    assert (_backup_dir(project) / "changelog-2026-03.jsonl").exists()


def test_interval_weekly_filename(project: Path) -> None:
    result = _result(project, interval="weekly")
    store_file = store_path(result)
    append_records(store_file, [make_entry("e1", "0.1.0")])
    # 2026-03-02 liegt in ISO-Woche 10.
    ensure_backup(result, store_file, now=_moment(2))
    assert (_backup_dir(project) / "changelog-2026-W10.jsonl").exists()


def test_backup_path_traversal_rejected(project: Path) -> None:
    result = _result(project, path="../evil")
    store_file = store_path(result)
    append_records(store_file, [make_entry("e1", "0.1.0")])
    with pytest.raises(SecurityError):
        ensure_backup(result, store_file, now=_moment(1))
