"""Low-level file operations with symlink and size guards.

Atomares Anhängen nutzt O_APPEND in genau einem write(), damit nebenläufige
Schreiber keine halben Zeilen verschränken.
"""

from __future__ import annotations

import os
from pathlib import Path

from .security import ensure_not_symlink, ensure_size_ok


def atomic_append(path: Path, data: str, encoding: str = "utf-8") -> None:
    """Append *data* to *path* in a single O_APPEND write.

    Creates the parent directory and the file if missing. Rejects symlinks.
    """
    ensure_not_symlink(path)
    ensure_size_ok(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = data.encode(encoding)
    # O_APPEND garantiert atomares Anhängen; genau ein write() pro Aufruf.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)


def read_text_lines(path: Path, encoding: str = "utf-8") -> list[str]:
    """Read *path* line by line. Missing file (ENOENT) returns an empty list."""
    if not path.exists():
        return []
    ensure_not_symlink(path)
    ensure_size_ok(path)
    with open(path, encoding=encoding) as handle:
        return handle.read().splitlines()


def read_text(path: Path, encoding: str = "utf-8") -> str:
    """Read the full text of *path*. Missing file returns an empty string."""
    if not path.exists():
        return ""
    ensure_not_symlink(path)
    ensure_size_ok(path)
    with open(path, encoding=encoding) as handle:
        return handle.read()


def write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path*, rejecting symlink targets."""
    ensure_not_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding, newline="\n") as handle:
        handle.write(content)


def touch_empty(path: Path) -> None:
    """Create an empty file (and parents). Rejects symlink targets."""
    ensure_not_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8"):
        pass
