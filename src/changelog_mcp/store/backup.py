"""Rotierendes Store-Backup (Sicherheitsnetz zusätzlich zum append-only Store).

Vor der ersten Änderung je Zeitraum (daily/weekly/monthly) wird der aktuelle
Store-Stand in den konfigurierten Backup-Ordner kopiert. Existiert die Datei des
Zeitraums bereits, passiert nichts (idempotent). Anschließend werden nur die
neuesten `retention` Backup-Dateien behalten; ältere werden entfernt.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ..config.loader import ConfigResult
from ..config.models import BackupConfig, BackupInterval
from ..utils.files import read_text, write_text
from ..utils.security import (
    ensure_not_symlink,
    resolve_within_root,
    validate_relative_path,
)

# Store ist immer UTF-8 (byte-stabil), unabhängig vom Markdown-Encoding.
STORE_ENCODING = "utf-8"
# Platzhalter im Dateiname-Muster, der durch die Zeitraum-Kennung ersetzt wird.
DATE_TOKEN = "{date}"


def _period_key(interval: BackupInterval, moment: datetime) -> str:
    """Sortierbare Zeitraum-Kennung: daily/weekly/monthly.

    Die Kennung ist so gewählt, dass lexikografische Sortierung der Dateinamen
    der chronologischen Reihenfolge entspricht.
    """
    if interval == "weekly":
        iso_year, iso_week, _ = moment.isocalendar()
        return str(iso_year) + "-W" + str(iso_week).zfill(2)
    if interval == "monthly":
        return moment.strftime("%Y-%m")
    return moment.strftime("%Y-%m-%d")


def _backup_filename(cfg: BackupConfig, moment: datetime) -> str:
    """Backup-Dateiname aus dem Muster und der Zeitraum-Kennung."""
    return cfg.file_format.replace(DATE_TOKEN, _period_key(cfg.interval, moment))


def _rotate(directory: Path, cfg: BackupConfig) -> None:
    """Nur die neuesten `retention` Backup-Dateien behalten, ältere löschen.

    Gematcht werden Dateien anhand des Prefix/Suffix um den {date}-Token.
    """
    prefix, _, suffix = cfg.file_format.partition(DATE_TOKEN)
    matches = [
        entry
        for entry in directory.iterdir()
        if entry.is_file()
        and entry.name.startswith(prefix)
        and entry.name.endswith(suffix)
        and len(entry.name) > len(prefix) + len(suffix)
    ]
    # Lexikografisch = chronologisch (ISO-Kennung); neueste am Ende.
    matches.sort(key=lambda p: p.name)
    for stale in matches[: max(0, len(matches) - cfg.retention)]:
        ensure_not_symlink(stale)
        stale.unlink()


def ensure_backup(
    result: ConfigResult,
    store_file: Path,
    now: datetime | None = None,
) -> Path | None:
    """Sichert den Store vor der ersten Änderung des Zeitraums; rotiert danach.

    Gibt den Pfad der (neu) erstellten Backup-Datei zurück, oder None, wenn
    nichts zu tun war (deaktiviert, Store fehlt/leer oder Backup existiert schon).
    """
    cfg = result.config.backup
    if not cfg.enabled:
        return None
    # Nur sichern, wenn es einen nicht-leeren Store zu sichern gibt.
    if not store_file.exists():
        return None
    content = read_text(store_file, encoding=STORE_ENCODING)
    if not content.strip():
        return None

    moment = now if now is not None else datetime.now(UTC)
    filename = _backup_filename(cfg, moment)
    # Pfad-/Traversal-/Symlink-Prüfung über die vorhandene Sicherheitsschicht.
    target = resolve_within_root(result.root, cfg.path, filename)
    if target.exists():
        return None

    write_text(target, content, encoding=STORE_ENCODING)
    # Backup-Ordner sicher auflösen und rotieren.
    validate_relative_path(cfg.path)
    directory = (result.root.resolve() / cfg.path).resolve()
    _rotate(directory, cfg)
    return target
