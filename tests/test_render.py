"""Render-Idempotenz und Render-Schutz."""

from __future__ import annotations

from pathlib import Path

from changelog_mcp.config.loader import changelog_path, full_changelog_path, load_config
from changelog_mcp.formats.registry import get_formatter
from changelog_mcp.render.markdown import render_all, render_full, render_public

from .conftest import make_entry, make_release


def _setup(project: Path):
    result = load_config(cwd=project)
    formatter = get_formatter(result.config.format)
    return result, formatter


def test_render_public_idempotent(project: Path) -> None:
    _, formatter = _setup(project)
    records = [make_entry("e-1", "0.1.0"), make_release("0.1.0", ["e-1"])]
    a = render_public(records, load_config(cwd=project).config, formatter)
    b = render_public(records, load_config(cwd=project).config, formatter)
    assert a == b
    assert "[0.1.0]" in a


def test_render_full_idempotent(project: Path) -> None:
    _, formatter = _setup(project)
    config = load_config(cwd=project).config
    records = [make_entry("e-1", "0.1.0"), make_entry("e-2", "0.1.1")]
    a = render_full(records, config, formatter)
    b = render_full(records, config, formatter)
    assert a == b


def test_protection_no_release_skips_public(project: Path) -> None:
    result, formatter = _setup(project)
    records = [make_entry("e-1", "0.1.0")]
    outcome = render_all(result, records, formatter)
    assert outcome.public_written is False
    assert outcome.full_written is True
    assert not changelog_path(result).exists()
    assert full_changelog_path(result).exists()


def test_render_writes_public_with_release(project: Path) -> None:
    result, formatter = _setup(project)
    records = [make_entry("e-1", "0.1.0"), make_release("0.1.0", ["e-1"])]
    outcome = render_all(result, records, formatter)
    assert outcome.public_written is True
    # Zweiter Lauf muss byte-identisch sein (Idempotenz auf Dateiebene).
    first = changelog_path(result).read_bytes()
    render_all(result, records, formatter)
    assert changelog_path(result).read_bytes() == first
