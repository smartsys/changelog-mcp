"""Tool render_changelog: beide Markdown-Dateien aus dem Store neu erzeugen."""

from __future__ import annotations

from pathlib import Path

from ..render.markdown import render_all
from .support import build_env, warnings_suffix


def render_changelog(cwd: Path | None = None) -> str:
    """Regenerate both markdown files from the store. Idempotent.

    Render-Schutz: die öffentliche CHANGELOG.md wird nicht geschrieben, solange
    kein Release existiert.
    """
    env = build_env(cwd)
    outcome = render_all(env.result, env.records, env.formatter)

    parts = [
        "CHANGELOG.md: "
        + ("geschrieben" if outcome.public_written else "übersprungen"),
        "CHANGELOG-full.md: "
        + ("geschrieben" if outcome.full_written else "deaktiviert"),
    ]
    message = "Rendering abgeschlossen. " + ", ".join(parts) + "."
    if outcome.note:
        message += " " + outcome.note
    return message + warnings_suffix(env.warnings)
