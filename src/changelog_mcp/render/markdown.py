"""Store -> CHANGELOG.md + CHANGELOG-full.md.

Idempotent: zweimaliges Rendern liefert byte-identische Dateien. Render-Schutz:
die öffentliche CHANGELOG.md wird nicht geschrieben, solange kein Release existiert.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config.loader import ConfigResult, changelog_path, full_changelog_path
from ..config.models import Config
from ..formats.base import ChangelogFormatter
from ..parser.version import parse_version
from ..store.jsonl import AnyRecord
from ..store.query import entries, releases
from ..utils.files import write_text


@dataclass
class RenderOutcome:
    """Result of a render pass: which files were written and why not."""

    public_written: bool
    full_written: bool
    note: str


def _join_blocks(header: str, blocks: list[str], spacing: int) -> str:
    """Join a header and blocks with *spacing* blank lines between blocks."""
    separator = "\n" * (spacing + 1)
    body = separator.join(blocks)
    if not blocks:
        # Nur Header (mit genau einem abschließenden Zeilenumbruch).
        return header.rstrip("\n") + "\n"
    return header.rstrip("\n") + "\n\n" + body + "\n"


def render_public(
    records: list[AnyRecord], config: Config, formatter: ChangelogFormatter
) -> str:
    """Render the curated CHANGELOG.md content (releases only, desc by version).

    Releases ohne öffentlichen Summary (reine Privat-Releases) werden übersprungen.
    """
    rels = sorted(
        releases(records), key=lambda r: (parse_version(r.version), r.ts), reverse=True
    )
    blocks = [formatter.format_release(r) for r in rels if r.summary]
    return _join_blocks(
        formatter.format_initial_changelog(), blocks, config.changelog.entry_spacing
    )


def render_full(
    records: list[AnyRecord], config: Config, formatter: ChangelogFormatter
) -> str:
    """Render the detailed CHANGELOG-full.md content (every entry, desc by version).

    Private Einträge bleiben aussen vor, solange fullChangelog.includePrivate=false.
    """
    include_private = config.full_changelog.include_private
    ents = [
        e for e in entries(records) if include_private or not e.private
    ]
    ents = sorted(ents, key=lambda e: (parse_version(e.version), e.ts), reverse=True)
    blocks = [formatter.format_entry(e) for e in ents]
    return _join_blocks(
        formatter.format_initial_changelog(), blocks, config.changelog.entry_spacing
    )


def render_full_only(
    result: ConfigResult,
    records: list[AnyRecord],
    formatter: ChangelogFormatter,
) -> bool:
    """Write only CHANGELOG-full.md from the store, if enabled.

    Für den Auto-Render nach jeder Mutation (add/edit/delete): die kuratierte
    CHANGELOG.md bleibt unberührt (sie entsteht erst bei create_release). Gibt
    zurück, ob die Detail-Datei geschrieben wurde.
    """
    config = result.config
    if not config.full_changelog.enabled:
        return False
    content = render_full(records, config, formatter)
    write_text(
        full_changelog_path(result), content, encoding=config.changelog.encoding
    )
    return True


def render_all(
    result: ConfigResult,
    records: list[AnyRecord],
    formatter: ChangelogFormatter,
) -> RenderOutcome:
    """Write both markdown files from the store.

    Render-Schutz: CHANGELOG.md wird nur geschrieben, wenn mindestens ein Release
    mit öffentlichem Summary existiert (sonst würde ein Render vor der Migration
    die Datei leeren; ein reines Privat-Release erzeugt keinen öffentlichen Block).
    """
    config = result.config
    has_public_release = any(r.summary for r in releases(records))

    public_written = False
    note = ""
    if has_public_release:
        content = render_public(records, config, formatter)
        write_text(changelog_path(result), content, encoding=config.changelog.encoding)
        public_written = True
    else:
        note = (
            "Öffentliche CHANGELOG.md nicht geschrieben: kein Release mit "
            "öffentlichem Summary im Store (Render-Schutz). Lösung: zuerst "
            "create_release mit Summary ausführen."
        )

    full_written = False
    if config.full_changelog.enabled:
        full_content = render_full(records, config, formatter)
        write_text(
            full_changelog_path(result),
            full_content,
            encoding=config.changelog.encoding,
        )
        full_written = True

    return RenderOutcome(public_written, full_written, note)
