"""End-to-End: init_changelog -> add_entry -> create_release -> render_changelog."""

from __future__ import annotations

from pathlib import Path

import pytest

from changelog_mcp.store.models import Section
from changelog_mcp.tools.add import add_entry
from changelog_mcp.tools.init import init_changelog
from changelog_mcp.tools.release import create_release, list_unreleased
from changelog_mcp.tools.version import get_current_version


def test_full_flow(project: Path) -> None:
    msg = init_changelog(cwd=project)
    assert "initialisiert" in msg
    # Store unter dem kanonischen Default-Pfad (Ordner wird angelegt);
    # Config im Projekt-Root.
    assert (project / "documentation" / "changelog" / "changelog.jsonl").exists()
    assert (project / "changelog-mcp-config.json").exists()

    add_entry("Added", "CSV-Export", files=["src/export.py"], cwd=project)
    add_entry("Fixed", "Absturz behoben", cwd=project)

    unreleased = list_unreleased(cwd=project)
    assert "0.1.1" in unreleased  # zweiter Eintrag bumpt auf 0.1.1

    summary = [Section(category="Added", items=["Export-Funktionen"])]
    result = create_release(summary, cwd=project)
    assert "Release 0.1.1 erstellt" in result

    changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "[0.1.1]" in changelog
    assert "Export-Funktionen" in changelog

    full = (project / "documentation" / "changelog" / "CHANGELOG-full.md").read_text(
        encoding="utf-8"
    )
    assert "CSV-Export" in full
    assert "Absturz behoben" in full

    current = get_current_version(cwd=project)
    assert "0.1.1" in current


def test_init_is_idempotent_and_keeps_store(project: Path) -> None:
    first = init_changelog(cwd=project)
    assert "initialisiert" in first
    add_entry("Added", "Bleibt erhalten", cwd=project)

    again = init_changelog(cwd=project)
    assert "initialisiert" in again
    # Store wird nie überschrieben, Config bleibt bestehen.
    assert "unverändert" in again
    assert "übernommen" in again
    assert "Bleibt erhalten" in list_unreleased(cwd=project)


def test_init_bootstraps_missing_env_config(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Henne-Ei-Falle: ENV zeigt auf eine Datei, die es noch nicht gibt.
    cfg = project / "cfg" / "changelog-mcp-config.json"
    monkeypatch.setenv("CHANGELOG_MCP_CONFIG", str(cfg))

    msg = init_changelog(cwd=project)
    assert "initialisiert" in msg
    assert cfg.exists()  # Config am ENV-Pfad angelegt
    # Folgeaufruf funktioniert jetzt (Config wird gefunden), kein harter Fehler.
    add_entry("Added", "Nach Bootstrap", cwd=project)
    assert "Nach Bootstrap" in list_unreleased(cwd=project)


def test_create_release_without_entries(project: Path) -> None:
    init_changelog(cwd=project)
    msg = create_release([Section(category="Added", items=["x"])], cwd=project)
    assert "Nichts unveröffentlicht" in msg
