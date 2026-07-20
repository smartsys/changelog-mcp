"""edit_entry und delete_entry: Ändern und Löschen per ID (append-only)."""

from __future__ import annotations

import re
from pathlib import Path

from changelog_mcp.store.models import Section
from changelog_mcp.tools.add import add_entry
from changelog_mcp.tools.edit import delete_entry, edit_entry
from changelog_mcp.tools.init import init_changelog
from changelog_mcp.tools.release import create_release, list_unreleased
from changelog_mcp.tools.search import search_entries


def _first_id(project: Path) -> str:
    """Erste Entry-ID aus list_unreleased extrahieren."""
    out = list_unreleased(cwd=project)
    match = re.search(r"- (e-\d+-[0-9a-f]+) \|", out)
    assert match is not None, out
    return match.group(1)


def test_list_unreleased_shows_id(project: Path) -> None:
    init_changelog(cwd=project)
    add_entry("Added", "CSV-Export", cwd=project)
    out = list_unreleased(cwd=project)
    assert re.search(r"e-\d+-[0-9a-f]+", out) is not None


def test_edit_changes_description(project: Path) -> None:
    init_changelog(cwd=project)
    add_entry("Added", "Alter Text", files=["src/a.py"], cwd=project)
    entry_id = _first_id(project)

    msg = edit_entry(entry_id, description="Neuer Text", cwd=project)
    assert "geändert" in msg

    hits = search_entries(query="Neuer", cwd=project)
    assert "Neuer Text" in hits
    # Alte Beschreibung ist nicht mehr auffindbar.
    assert "Keine Treffer" in search_entries(query="Alter", cwd=project)


def test_edit_only_named_fields(project: Path) -> None:
    init_changelog(cwd=project)
    add_entry("Added", "Text", files=["src/keep.py"], cwd=project)
    entry_id = _first_id(project)

    edit_entry(entry_id, category="Fixed", cwd=project)
    hits = search_entries(file="keep.py", cwd=project)
    # Kategorie geändert, Dateien unverändert.
    assert "[Fixed]" in hits
    assert "src/keep.py" in hits


def test_edit_unknown_id(project: Path) -> None:
    init_changelog(cwd=project)
    msg = edit_entry("e-0-0000", description="x", cwd=project)
    assert "nicht gefunden" in msg


def test_edit_without_fields(project: Path) -> None:
    init_changelog(cwd=project)
    add_entry("Added", "Text", cwd=project)
    entry_id = _first_id(project)
    msg = edit_entry(entry_id, cwd=project)
    assert "Keine Änderung" in msg


def test_edit_invalid_category_rejected(project: Path) -> None:
    # Explizit striktes Format: Default ist inzwischen 'smart' (nicht strikt).
    init_changelog(fmt="keep-a-changelog", cwd=project)
    add_entry("Added", "Text", cwd=project)
    entry_id = _first_id(project)
    # keep-a-changelog ist strikt -> unbekannte Kategorie wird abgelehnt.
    try:
        edit_entry(entry_id, category="Unbekannt", cwd=project)
    except Exception as exc:  # FormatError
        assert "Ungültige Kategorie" in str(exc)
    else:
        raise AssertionError("Ungültige Kategorie wurde nicht abgelehnt")


def test_delete_removes_entry(project: Path) -> None:
    init_changelog(cwd=project)
    add_entry("Added", "Wegwerf", cwd=project)
    entry_id = _first_id(project)

    msg = delete_entry(entry_id, cwd=project)
    assert "gelöscht" in msg
    assert "Keine unveröffentlichten" in list_unreleased(cwd=project)


def test_delete_released_entry_rejected(project: Path) -> None:
    init_changelog(cwd=project)
    add_entry("Added", "Bleibt", cwd=project)
    entry_id = _first_id(project)
    create_release([Section(category="Added", items=["Release"])], cwd=project)

    msg = delete_entry(entry_id, cwd=project)
    assert "abgelehnt" in msg


def test_delete_unknown_id(project: Path) -> None:
    init_changelog(cwd=project)
    msg = delete_entry("e-0-0000", cwd=project)
    assert "nicht gefunden" in msg


def _full(project: Path) -> str:
    """Inhalt von CHANGELOG-full.md lesen."""
    return (project / "documentation" / "changelog" / "CHANGELOG-full.md").read_text(
        encoding="utf-8"
    )


def test_add_auto_renders_full(project: Path) -> None:
    """add_entry aktualisiert CHANGELOG-full.md sofort, ohne render_changelog."""
    init_changelog(cwd=project)
    add_entry("Added", "Auto-Render-Feature", cwd=project)

    assert "Auto-Render-Feature" in _full(project)
    # Render-Schutz: ohne Release entsteht keine kuratierte CHANGELOG.md.
    assert not (project / "CHANGELOG.md").exists()


def test_edit_auto_renders_full(project: Path) -> None:
    """edit_entry aktualisiert CHANGELOG-full.md sofort, ohne render_changelog."""
    init_changelog(cwd=project)
    add_entry("Added", "Alt", cwd=project)
    entry_id = _first_id(project)

    edit_entry(entry_id, description="Neu poliert", cwd=project)
    full = _full(project)
    assert "Neu poliert" in full
    assert "Alt" not in full


def test_delete_auto_renders_full(project: Path) -> None:
    """delete_entry entfernt den Eintrag sofort aus CHANGELOG-full.md."""
    init_changelog(cwd=project)
    add_entry("Added", "Wegwerf-Detail", cwd=project)
    entry_id = _first_id(project)

    delete_entry(entry_id, cwd=project)
    assert "Wegwerf-Detail" not in _full(project)


def test_corrections_survive_render(project: Path) -> None:
    """Edit + Delete wirken sich auf das gerenderte Markdown aus."""
    init_changelog(cwd=project)
    add_entry("Added", "Feature A", cwd=project)
    keep_id = _first_id(project)
    add_entry("Added", "Feature B zum Loeschen", cwd=project)

    # Zweiten Eintrag (B) per Suche finden und löschen.
    hits = search_entries(query="Feature B", cwd=project)
    b_id = re.search(r"(e-\d+-[0-9a-f]+)", hits).group(1)
    delete_entry(b_id, cwd=project)
    edit_entry(keep_id, description="Feature A neu", cwd=project)

    create_release([Section(category="Added", items=["Erstes Release"])], cwd=project)
    full = (project / "documentation" / "changelog" / "CHANGELOG-full.md").read_text(
        encoding="utf-8"
    )
    assert "Feature A neu" in full
    assert "Feature B" not in full
