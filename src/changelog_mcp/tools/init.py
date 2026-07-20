"""Tool init_changelog: Store + Config anlegen (idempotenter Bootstrap)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from ..config.loader import ConfigResult, bootstrap_target, store_path
from ..config.models import Config, FormatName
from ..formats.registry import get_formatter
from ..utils.files import touch_empty, write_text


def init_changelog(fmt: str | None = None, cwd: Path | None = None) -> str:
    """Bootstrap the changelog for a project: ensure store and config exist.

    Idempotent: eine vorhandene Config wird übernommen, ein vorhandener Store nie
    überschrieben. Der Config-Zielpfad kommt aus CHANGELOG_MCP_CONFIG (falls gesetzt),
    sonst ein Default-Name im Projekt-Root — so landet die Datei dort, wo der Client
    sie erwartet. Angelegt wird nur, was fehlt.
    """
    root, config_target, existing = bootstrap_target(cwd)

    if existing is not None:
        # Vorhandene Config nehmen, nicht überschreiben.
        result = existing
        chosen = existing.config.format
        config_note = (
            "Vorhandene Konfiguration übernommen ('" + str(config_target) + "')."
        )
        if fmt is not None and fmt != chosen:
            config_note += (
                " Hinweis: Format-Parameter '" + fmt + "' ignoriert (Config existiert)."
            )
    else:
        requested = fmt if fmt is not None else Config().format
        # Format validieren (unbekannter Name -> klarer deutscher Fehler).
        get_formatter(requested)
        # Nach get_formatter ist requested nachweislich ein gültiger Formatname.
        chosen = cast(FormatName, requested)
        result = ConfigResult(Config(format=chosen), root, None, True)

    store_file = store_path(result)
    if store_file.exists():
        store_note = "Store bereits vorhanden ('" + str(store_file) + "'), unverändert."
    else:
        touch_empty(store_file)
        store_note = "Store angelegt ('" + str(store_file) + "')."

    if existing is None:
        write_text(
            config_target,
            json.dumps(result.config.to_json_dict(), ensure_ascii=False, indent=2)
            + "\n",
        )
        config_note = "Konfiguration angelegt ('" + str(config_target) + "')."

    return (
        "Changelog initialisiert. " + store_note + " " + config_note
        + " Format: '" + chosen + "'. Markdown-Dateien entstehen beim ersten "
        "create_release."
    )
