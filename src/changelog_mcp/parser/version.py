"""SemVer bump und toleranter Vergleich (Modi semver / patch-only).

Nicht parsebare Komponenten zählen als 0, damit ein defekter Wert niedrig
sortiert statt eine Exception zu werfen. Der Store muss lesbar bleiben.
"""

from __future__ import annotations

Bump = str  # "major" | "minor" | "patch"
FALLBACK_VERSION = "0.0.0"


def parse_version(value: str) -> tuple[int, int, int]:
    """Parse 'X.Y.Z' tolerantly. Non-numeric components count as 0."""
    parts = (value or "").strip().lstrip("vV").split(".")

    def _num(index: int) -> int:
        if index >= len(parts):
            return 0
        try:
            return int(parts[index])
        except (ValueError, TypeError):
            return 0

    return (_num(0), _num(1), _num(2))


def compare_versions(a: str, b: str) -> int:
    """Return -1/0/1 comparing two versions tolerantly."""
    pa, pb = parse_version(a), parse_version(b)
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def initial_version(fixed_major: int | None, fixed_minor: int | None) -> str:
    """Initial version for an empty store: {major??0}.{minor??1}.0 -> default 0.1.0."""
    major = fixed_major if fixed_major is not None else 0
    minor = fixed_minor if fixed_minor is not None else 1
    return f"{major}.{minor}.0"


def _bump_semver(current: str, bump: Bump) -> str:
    major, minor, patch = parse_version(current)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    # Default patch.
    return f"{major}.{minor}.{patch + 1}"


def _bump_patch_only(
    current: str, fixed_major: int | None, fixed_minor: int | None
) -> str:
    """patch-only: fester Major/Minor, nur Patch zählt hoch.

    Ändert sich Major/Minor gegenüber der aktuellen Version, wird auf .1 zurückgesetzt.
    """
    major = fixed_major if fixed_major is not None else 0
    minor = fixed_minor if fixed_minor is not None else 1
    cur_major, cur_minor, cur_patch = parse_version(current)
    if cur_major == major and cur_minor == minor:
        return f"{major}.{minor}.{cur_patch + 1}"
    # Major/Minor hat sich geändert -> Patch auf 1 zurücksetzen.
    return f"{major}.{minor}.1"


def next_version(
    current: str,
    bump: Bump,
    mode: str,
    fixed_major: int | None,
    fixed_minor: int | None,
) -> str:
    """Compute the next version from *current* under the given versioning mode."""
    if mode == "patch-only":
        return _bump_patch_only(current, fixed_major, fixed_minor)
    return _bump_semver(current, bump)
