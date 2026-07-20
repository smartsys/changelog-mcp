"""Config-Auflösung und get_config."""

from __future__ import annotations

import json
from pathlib import Path

from changelog_mcp.config.loader import load_config
from changelog_mcp.tools.config import get_config


def test_zero_config_defaults(project: Path) -> None:
    result = load_config(cwd=project)
    assert result.using_defaults is True
    assert result.config.format == "smart"
    assert result.loaded_from is None


def test_config_file_in_cwd_is_used(project: Path) -> None:
    (project / "changelog-mcp-config.json").write_text(
        json.dumps({"format": "smart"}), encoding="utf-8"
    )
    result = load_config(cwd=project)
    assert result.using_defaults is False
    assert result.config.format == "smart"


def test_env_var_takes_precedence(project: Path) -> None:
    cfg = project / "custom.json"
    cfg.write_text(json.dumps({"format": "conventional"}), encoding="utf-8")
    result = load_config(cwd=project, env={"CHANGELOG_MCP_CONFIG": str(cfg)})
    assert result.config.format == "conventional"
    assert result.loaded_from == str(cfg)


def test_get_config_returns_json(project: Path) -> None:
    out = get_config(cwd=project)
    data = json.loads(out)
    assert data["usingDefaults"] is True
    assert data["config"]["format"] == "smart"
    # camelCase-Aliase müssen erhalten bleiben (byte-stabil).
    assert "dateFormat" in data["config"]
    assert "fullChangelog" in data["config"]
