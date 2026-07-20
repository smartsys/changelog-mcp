"""Versionslogik: beide Modi und toleranter Vergleich."""

from __future__ import annotations

from changelog_mcp.parser.version import (
    compare_versions,
    initial_version,
    next_version,
    parse_version,
)


def test_tolerant_parse_non_numeric_is_zero() -> None:
    assert parse_version("1.x.3") == (1, 0, 3)
    assert parse_version("kaputt") == (0, 0, 0)
    assert parse_version("v2.5.7") == (2, 5, 7)


def test_compare_versions() -> None:
    assert compare_versions("1.2.0", "1.10.0") == -1
    assert compare_versions("2.0.0", "1.9.9") == 1
    assert compare_versions("1.1.1", "1.1.1") == 0


def test_semver_bumps() -> None:
    assert next_version("1.2.3", "patch", "semver", None, None) == "1.2.4"
    assert next_version("1.2.3", "minor", "semver", None, None) == "1.3.0"
    assert next_version("1.2.3", "major", "semver", None, None) == "2.0.0"


def test_patch_only_increments_patch() -> None:
    assert next_version("0.1.5", "patch", "patch-only", 0, 1) == "0.1.6"
    # bump-Parameter wird im patch-only-Modus ignoriert.
    assert next_version("0.1.5", "major", "patch-only", 0, 1) == "0.1.6"


def test_patch_only_resets_when_fixed_changes() -> None:
    # Aktuelle Version hat anderen Minor als die feste Config -> Reset auf .1.
    assert next_version("0.2.9", "patch", "patch-only", 0, 1) == "0.1.1"


def test_initial_version_defaults() -> None:
    assert initial_version(None, None) == "0.1.0"
    assert initial_version(2, 3) == "2.3.0"
