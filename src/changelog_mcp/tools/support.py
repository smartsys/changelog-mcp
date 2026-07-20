"""Gemeinsame Tool-Infrastruktur: frisches Laden von Config + Store.

Kein In-Memory-State zwischen Aufrufen — jeder Tool-Aufruf liest Config und Store
frisch vom Dateisystem.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from ..config.loader import ConfigResult, load_config, store_path
from ..formats.base import ChangelogFormatter
from ..formats.registry import get_formatter
from ..render.markdown import render_full_only
from ..store.backup import ensure_backup
from ..store.jsonl import (
    AnyRecord,
    ReadResult,
    WritableRecord,
    append_records,
    read_store,
)

# Store ist immer UTF-8 (byte-stabil), unabhängig vom Markdown-Encoding.
STORE_ENCODING = "utf-8"


@dataclass
class ToolEnv:
    """Fresh view of config, formatter and store for a single tool call."""

    result: ConfigResult
    formatter: ChangelogFormatter
    records: list[AnyRecord]
    warnings: list[str]
    store_file: Path


def build_env(cwd: Path | None = None) -> ToolEnv:
    """Load config, resolve the formatter and read the store fresh."""
    result = load_config(cwd)
    config = result.config
    formatter = get_formatter(config.format, config.versioning.prefix)
    store_file = store_path(result)
    read: ReadResult = read_store(store_file, encoding=STORE_ENCODING)
    return ToolEnv(result, formatter, read.records, read.warnings, store_file)


def write_records(env: ToolEnv, records: list[WritableRecord]) -> None:
    """Sichert den Store (Backup je Zeitraum) und hängt dann die Records an.

    Zentraler Schreibpfad aller schreibenden Tools: das Backup entsteht vor dem
    ersten Write des Zeitraums, danach erfolgt das atomare Anhängen.
    """
    ensure_backup(env.result, env.store_file)
    append_records(env.store_file, records, encoding=STORE_ENCODING)


def rerender_full(cwd: Path | None = None) -> bool:
    """Nach einem Append den Store frisch lesen und CHANGELOG-full.md neu rendern.

    Wird von den mutierenden Tools (add/edit/delete) direkt nach write_records
    aufgerufen, damit die Detail-Datei jederzeit aktuell ist. Der Store muss frisch
    geladen werden, weil env.records den soeben angehängten Record noch nicht kennt.
    Gibt zurück, ob die Datei geschrieben wurde (false bei deaktivierter Detail-Datei).
    """
    fresh = build_env(cwd)
    return render_full_only(fresh.result, fresh.records, fresh.formatter)


def new_entry_id() -> str:
    """Generate a unique entry id in the form e-{millis}-{hex}."""
    millis = int(time.time() * 1000)
    return "e-" + str(millis) + "-" + secrets.token_hex(2)


def warnings_suffix(warnings: list[str]) -> str:
    """Return a formatted warning block, or an empty string."""
    if not warnings:
        return ""
    return "\n\nWarnungen:\n- " + "\n- ".join(warnings)
