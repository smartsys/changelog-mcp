"""Tool get_config: aktive, aufgelöste Konfiguration anzeigen."""

from __future__ import annotations

import json
from pathlib import Path

from ..config.loader import load_config


def get_config(cwd: Path | None = None) -> str:
    """Show the active resolved configuration as JSON plus its provenance."""
    result = load_config(cwd)
    payload = {
        "config": result.config.to_json_dict(),
        "usingDefaults": result.using_defaults,
        "loadedFrom": result.loaded_from,
        "root": str(result.root),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
