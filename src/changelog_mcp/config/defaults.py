"""Default-Konfiguration (Zero-Config-Fallback)."""

from __future__ import annotations

from .models import Config

# Dateinamen, unter denen eine Config im Projekt gesucht wird.
CONFIG_FILENAMES = ("changelog-mcp-config.json", ".changelog-mcp.json")

# Name der Umgebungsvariable mit explizitem Config-Pfad.
CONFIG_ENV_VAR = "CHANGELOG_MCP_CONFIG"


def default_config() -> Config:
    """Return the Zero-Config default configuration (all defaults)."""
    return Config()
