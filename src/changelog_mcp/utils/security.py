"""Path-Traversal-, Symlink- und Größen-Schutz (Defense-in-Depth).

Alle Config-Pfade sind relativ zum Projekt-Root. Absolute Pfade, '..'-Segmente
und Null-Bytes werden abgelehnt; aufgelöste Pfade müssen im Root bleiben.
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

# Größenlimit pro Changelog-Datei: 10 MB.
MAX_CHANGELOG_SIZE = 10 * 1024 * 1024


class SecurityError(Exception):
    """Raised when a path fails a security check."""


def validate_relative_path(rel: str) -> None:
    """Validate that *rel* is a safe, relative path within the project root.

    Rejects absolute paths, '..' segments and null bytes.
    """
    if rel is None or rel == "":
        raise SecurityError(
            "Leerer Pfad übergeben. Kontext: Konfiguration erwartet einen "
            "relativen Pfad. Lösung: einen relativen Pfad wie './' angeben."
        )
    if "\x00" in rel:
        raise SecurityError(
            "Pfad enthält ein Null-Byte. Kontext: '" + repr(rel) + "'. "
            "Lösung: Null-Bytes aus dem Pfad entfernen."
        )
    # Backslashes zu Slashes normalisieren, damit '..' auch unter Windows greift.
    normalized = rel.replace("\\", "/")
    if PurePosixPath(normalized).is_absolute() or (len(rel) > 1 and rel[1] == ":"):
        raise SecurityError(
            "Absoluter Pfad ist nicht erlaubt: '" + rel + "'. "
            "Lösung: einen relativen Pfad zum Projekt-Root verwenden."
        )
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise SecurityError(
            "Pfad enthält '..'-Segmente: '" + rel + "'. "
            "Lösung: Path-Traversal ist verboten, relativen Pfad ohne '..' angeben."
        )


def validate_filename(name: str) -> None:
    """Validate a bare filename: no '/', '\\', '..' or null byte."""
    if not name:
        raise SecurityError(
            "Leerer Dateiname. Lösung: einen gültigen Dateinamen angeben."
        )
    if "\x00" in name:
        raise SecurityError(
            "Dateiname enthält ein Null-Byte. Lösung: Null-Byte entfernen."
        )
    if "/" in name or "\\" in name or ".." in name:
        raise SecurityError(
            "Ungültiger Dateiname: '" + name + "'. Kontext: enthält '/', '\\\\' "
            "oder '..'. Lösung: reinen Dateinamen ohne Pfadanteile verwenden."
        )


def resolve_within_root(root: Path, rel_dir: str, filename: str) -> Path:
    """Resolve *rel_dir*/*filename* under *root* and ensure it stays inside.

    Returns the absolute target path. Raises SecurityError on traversal.
    """
    validate_relative_path(rel_dir)
    validate_filename(filename)
    root_resolved = root.resolve()
    target = (root_resolved / rel_dir / filename).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise SecurityError(
            "Aufgelöster Pfad liegt außerhalb des Projekt-Roots: '"
            + str(target) + "'. Root: '" + str(root_resolved) + "'. "
            "Lösung: Pfad innerhalb des Projekts wählen."
        ) from exc
    return target


def resolve_source_file(root: Path, rel: str) -> Path:
    """Resolve a source file (relative to root) for read-only access."""
    validate_relative_path(rel)
    root_resolved = root.resolve()
    target = (root_resolved / rel).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise SecurityError(
            "Quelldatei liegt außerhalb des Projekt-Roots: '" + str(target)
            + "'. Lösung: relativen Pfad innerhalb des Projekts angeben."
        ) from exc
    return target


def ensure_not_symlink(path: Path) -> None:
    """Ensure *path* (if it exists) is not a symlink before I/O."""
    if path.is_symlink():
        raise SecurityError(
            "Ziel ist ein Symlink: '" + str(path) + "'. Kontext: Symlinks werden "
            "vor Lese-/Schreibzugriff abgelehnt. Lösung: echte Datei verwenden."
        )


def ensure_size_ok(path: Path) -> None:
    """Ensure an existing file does not exceed MAX_CHANGELOG_SIZE."""
    if path.exists() and not path.is_symlink():
        size = os.path.getsize(path)
        if size > MAX_CHANGELOG_SIZE:
            raise SecurityError(
                "Datei überschreitet das Größenlimit ("
                + str(MAX_CHANGELOG_SIZE) + " Bytes): '" + str(path) + "' hat "
                + str(size) + " Bytes. Lösung: Store bereinigen oder Limit prüfen."
            )
