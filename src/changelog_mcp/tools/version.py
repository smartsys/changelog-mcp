"""Tools get_current_version und get_next_version."""

from __future__ import annotations

from pathlib import Path

from ..parser.version import initial_version, next_version
from ..store.query import has_any_version, highest_version, unreleased_entries
from .support import build_env, warnings_suffix


def get_current_version(cwd: Path | None = None) -> str:
    """Highest version across entries and releases; unreleased count included."""
    env = build_env(cwd)
    unreleased_count = len(unreleased_entries(env.records))

    if not has_any_version(env.records):
        versioning = env.result.config.versioning
        initial = initial_version(versioning.fixed_major, versioning.fixed_minor)
        return (
            "Aktuelle Version: 0.0.0 (leerer Store). Die erste erfasste Version "
            "wäre " + initial + ". Unveröffentlichte Einträge: "
            + str(unreleased_count) + "." + warnings_suffix(env.warnings)
        )

    version = highest_version(env.records)
    return (
        "Aktuelle Version: " + version + ". Unveröffentlichte Einträge: "
        + str(unreleased_count) + "." + warnings_suffix(env.warnings)
    )


def get_next_version(bump: str = "patch", cwd: Path | None = None) -> str:
    """Compute the next version from the highest store version and the mode."""
    env = build_env(cwd)
    versioning = env.result.config.versioning

    if not has_any_version(env.records):
        version = initial_version(versioning.fixed_major, versioning.fixed_minor)
    else:
        version = next_version(
            highest_version(env.records),
            bump,
            versioning.mode,
            versioning.fixed_major,
            versioning.fixed_minor,
        )
    return (
        "Nächste Version (" + bump + ", Modus " + versioning.mode + "): "
        + version + "." + warnings_suffix(env.warnings)
    )
