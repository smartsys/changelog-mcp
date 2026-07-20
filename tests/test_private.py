"""Private Einträge: Sichtbarkeit in Quelle, Rendern und Release-Flow."""

from __future__ import annotations

from pathlib import Path

from changelog_mcp.config.loader import (
    changelog_path,
    full_changelog_path,
    load_config,
)
from changelog_mcp.config.models import Config, FullChangelogConfig
from changelog_mcp.formats.registry import get_formatter
from changelog_mcp.render.markdown import render_full, render_public
from changelog_mcp.store.models import Section
from changelog_mcp.store.query import public_unreleased_entries
from changelog_mcp.tools.add import add_entry
from changelog_mcp.tools.release import create_release, list_unreleased

from .conftest import make_entry, make_release


def _formatter():
    return get_formatter("smart")


# -- Quelle: public_unreleased_entries -----------------------------------
def test_public_unreleased_hides_private_by_default() -> None:
    records = [
        make_entry("e-1", "0.1.0"),
        make_entry("e-2", "0.1.1", private=True),
    ]
    visible = public_unreleased_entries(records, include_private=False)
    assert [e.id for e in visible] == ["e-1"]


def test_public_unreleased_includes_private_with_flag() -> None:
    records = [
        make_entry("e-1", "0.1.0"),
        make_entry("e-2", "0.1.1", private=True),
    ]
    visible = public_unreleased_entries(records, include_private=True)
    assert [e.id for e in visible] == ["e-1", "e-2"]


# -- render_full ---------------------------------------------------------
def test_render_full_hides_private_by_default() -> None:
    config = Config()  # fullChangelog.includePrivate = False
    records = [
        make_entry("e-1", "0.1.0", description="Oeffentlich"),
        make_entry("e-2", "0.1.1", description="Geheim", private=True),
    ]
    out = render_full(records, config, _formatter())
    assert "Oeffentlich" in out
    assert "Geheim" not in out


def test_render_full_includes_private_with_flag() -> None:
    config = Config(full_changelog=FullChangelogConfig(include_private=True))
    records = [
        make_entry("e-1", "0.1.0", description="Oeffentlich"),
        make_entry("e-2", "0.1.1", description="Geheim", private=True),
    ]
    out = render_full(records, config, _formatter())
    assert "Oeffentlich" in out
    assert "Geheim" in out


# -- render_public -------------------------------------------------------
def test_render_public_skips_private_only_release() -> None:
    config = Config()
    # Release ohne Summary (reines Privat-Release) darf keinen Block erzeugen.
    release = make_release("0.1.0", ["e-1"])
    release.summary = []
    out = render_public(
        [make_entry("e-1", "0.1.0", private=True), release], config, _formatter()
    )
    assert "[0.1.0]" not in out


# -- Tool-Flow: list_unreleased + create_release -------------------------
def test_release_flow_excludes_private(project: Path) -> None:
    add_entry("Added", "Oeffentliche Funktion", cwd=project)
    add_entry("Fixed", "Interner Doku-Fix", private=True, cwd=project)

    listing = list_unreleased(cwd=project)
    assert "Oeffentliche Funktion" in listing
    assert "Interner Doku-Fix" not in listing
    assert "1 private" in listing

    create_release(
        summary=[Section(category="Added", items=["Oeffentliche Funktion"])],
        cwd=project,
    )
    result = load_config(cwd=project)
    public = changelog_path(result).read_text(encoding="utf-8")
    full = full_changelog_path(result).read_text(encoding="utf-8")
    assert "Oeffentliche Funktion" in public
    assert "Interner Doku-Fix" not in public
    # CHANGELOG-full.md filtert privat ebenfalls (Default).
    assert "Interner Doku-Fix" not in full


def test_private_only_release_needs_no_summary(project: Path) -> None:
    add_entry("Fixed", "Nur interner Kram", private=True, cwd=project)
    # Ohne Summary erlaubt, da keine oeffentlichen Eintraege offen sind.
    msg = create_release(cwd=project)
    assert "erstellt" in msg
    result = load_config(cwd=project)
    # Kein oeffentlicher Block -> CHANGELOG.md nicht geschrieben (Render-Schutz greift,
    # da kein Release mit Summary existiert).
    assert not changelog_path(result).exists()
