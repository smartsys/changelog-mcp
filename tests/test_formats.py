"""Format-Kategorienvalidierung: strikt (keep/conventional) vs. frei (smart)."""

from __future__ import annotations

import pytest

from changelog_mcp.formats.base import FormatError
from changelog_mcp.formats.registry import available_formats, get_formatter


def test_keep_a_changelog_rejects_unknown_category() -> None:
    formatter = get_formatter("keep-a-changelog")
    formatter.validate_category("Added")  # gültig
    with pytest.raises(FormatError):
        formatter.validate_category("Erfunden")


def test_conventional_strict() -> None:
    formatter = get_formatter("conventional")
    formatter.validate_category("Features")
    with pytest.raises(FormatError):
        formatter.validate_category("Added")


def test_smart_accepts_any_category() -> None:
    formatter = get_formatter("smart")
    formatter.validate_category("Added")
    formatter.validate_category("VölligFrei")  # akzeptiert


def test_unknown_format_raises_with_available_list() -> None:
    with pytest.raises(FormatError) as exc:
        get_formatter("gibtsnicht")
    for name in available_formats():
        assert name in str(exc.value)


def test_version_headings_per_format() -> None:
    assert get_formatter("keep-a-changelog").version_heading("1.0.0", "2026-07-13") == (
        "## [1.0.0] - 2026-07-13"
    )
    assert get_formatter("conventional").version_heading("1.0.0", "2026-07-13") == (
        "## 1.0.0 (2026-07-13)"
    )
    assert get_formatter("smart").version_heading("1.0.0", "2026-07-13") == (
        "## [1.0.0] - 2026-07-13"
    )
