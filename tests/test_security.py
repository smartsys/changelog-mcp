"""Security: Path-Traversal und Symlinks werden abgelehnt."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from changelog_mcp.utils.files import atomic_append
from changelog_mcp.utils.security import (
    SecurityError,
    ensure_not_symlink,
    resolve_within_root,
    validate_filename,
    validate_relative_path,
)


def test_relative_path_rejects_absolute() -> None:
    with pytest.raises(SecurityError):
        validate_relative_path("/etc")


def test_relative_path_rejects_dotdot() -> None:
    with pytest.raises(SecurityError):
        validate_relative_path("../outside")


def test_filename_rejects_separators() -> None:
    with pytest.raises(SecurityError):
        validate_filename("../evil")
    with pytest.raises(SecurityError):
        validate_filename("sub/dir")


def test_resolve_within_root_blocks_traversal(project: Path) -> None:
    with pytest.raises(SecurityError):
        resolve_within_root(project, "..", "changelog.jsonl")


def test_resolve_within_root_ok(project: Path) -> None:
    target = resolve_within_root(project, "./", "changelog.jsonl")
    assert str(target).startswith(str(project.resolve()))


@pytest.mark.skipif(os.name == "nt", reason="Symlinks unter Windows eingeschränkt")
def test_symlink_is_rejected(project: Path) -> None:
    real = project / "real.jsonl"
    real.write_text("{}", encoding="utf-8")
    link = project / "link.jsonl"
    link.symlink_to(real)
    with pytest.raises(SecurityError):
        ensure_not_symlink(link)
    with pytest.raises(SecurityError):
        atomic_append(link, "x\n")
