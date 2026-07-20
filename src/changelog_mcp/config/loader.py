"""Config-Auflösung: ENV -> CWD -> Git-Root -> Zero-Config-Defaults.

Der Loader liefert immer die aufgelöste Config plus Metadaten (woher geladen,
ob Defaults aktiv sind) und den Projekt-Root für die Pfad-Auflösung.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from ..utils.security import ensure_not_symlink, resolve_within_root
from .defaults import CONFIG_ENV_VAR, CONFIG_FILENAMES, default_config
from .models import Config


class ConfigError(Exception):
    """Raised when a config file is invalid JSON or violates the schema."""


@dataclass
class ConfigResult:
    """Resolved configuration plus provenance metadata."""

    config: Config
    root: Path
    loaded_from: str | None
    using_defaults: bool


def git_root(cwd: Path) -> Path | None:
    """Return the git top-level directory for *cwd*, or None if not a repo."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    top = out.stdout.strip()
    return Path(top) if top else None


def _load_file(path: Path) -> Config:
    """Load and validate a config file. Raises ConfigError with German text."""
    ensure_not_symlink(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(
            "Konfigurationsdatei konnte nicht gelesen werden: '" + str(path)
            + "'. Lösung: Dateizugriff und Pfad prüfen."
        ) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            "Ungültiges JSON in der Konfiguration: '" + str(path) + "' (Zeile "
            + str(exc.lineno) + ", Spalte " + str(exc.colno) + "). "
            "Lösung: JSON-Syntax korrigieren."
        ) from exc
    try:
        return Config.model_validate(data)
    except ValidationError as exc:
        fields = ", ".join(".".join(str(p) for p in e["loc"]) for e in exc.errors())
        raise ConfigError(
            "Konfiguration verletzt das Schema: '" + str(path) + "'. Betroffene "
            "Felder: " + fields + ". Lösung: Felder gemäß Konfigurationsdoku "
            "im README (Abschnitt Konfiguration) anpassen."
        ) from exc


def _resolve_root(cwd: Path) -> Path:
    """Project root for path resolution: git root if available, else cwd."""
    top = git_root(cwd)
    return top if top is not None else cwd


def _find_in_dir(directory: Path) -> Path | None:
    """Return the first existing config file in *directory*, or None."""
    for name in CONFIG_FILENAMES:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def load_config(
    cwd: Path | None = None, env: Mapping[str, str] | None = None
) -> ConfigResult:
    """Resolve the configuration following the documented chain.

    1. CHANGELOG_MCP_CONFIG (explicit path)
    2. config file in the current working directory
    3. config file in the git root
    4. Zero-Config defaults
    """
    cwd = Path(cwd) if cwd is not None else Path(os.getcwd())
    environ: Mapping[str, str] = env if env is not None else os.environ
    root = _resolve_root(cwd)

    env_path = environ.get(CONFIG_ENV_VAR)
    if env_path:
        candidate = Path(env_path)
        if not candidate.is_file():
            raise ConfigError(
                "In " + CONFIG_ENV_VAR + " angegebene Konfiguration fehlt: '"
                + env_path + "'. Lösung: zuerst init_changelog ausführen (legt die "
                "Datei an diesem Pfad an), oder den Pfad korrigieren bzw. die "
                "Variable entfernen."
            )
        return ConfigResult(_load_file(candidate), root, str(candidate), False)

    found = _find_in_dir(cwd)
    if found is None and root != cwd:
        found = _find_in_dir(root)
    if found is not None:
        return ConfigResult(_load_file(found), root, str(found), False)

    return ConfigResult(default_config(), root, None, True)


def bootstrap_target(
    cwd: Path | None = None, env: Mapping[str, str] | None = None
) -> tuple[Path, Path, ConfigResult | None]:
    """For init_changelog: project root, intended config path and any existing config.

    Anders als load_config wirft dies NICHT, wenn eine per ENV angegebene Datei
    fehlt — genau diesen Fall soll init bootstrappen (die Datei anlegen).

    - target: wohin eine neue Config geschrieben würde (ENV-Wert, sonst Default-Name
      im Projekt-Root).
    - existing: geladene ConfigResult, falls bereits eine Config existiert, sonst None.
    """
    cwd = Path(cwd) if cwd is not None else Path(os.getcwd())
    environ: Mapping[str, str] = env if env is not None else os.environ
    root = _resolve_root(cwd)

    env_path = environ.get(CONFIG_ENV_VAR)
    if env_path:
        target = Path(env_path)
        if target.is_file():
            return root, target, ConfigResult(
                _load_file(target), root, str(target), False
            )
        return root, target, None

    found = _find_in_dir(cwd)
    if found is None and root != cwd:
        found = _find_in_dir(root)
    if found is not None:
        return root, found, ConfigResult(_load_file(found), root, str(found), False)

    return root, root / CONFIG_FILENAMES[0], None


def store_path(result: ConfigResult) -> Path:
    """Resolve the absolute store path within the project root."""
    cfg = result.config.store
    return resolve_within_root(result.root, cfg.path, cfg.file)


def changelog_path(result: ConfigResult) -> Path:
    """Resolve the absolute public CHANGELOG.md path within the project root."""
    cfg = result.config.changelog
    return resolve_within_root(result.root, cfg.path, cfg.file)


def full_changelog_path(result: ConfigResult) -> Path:
    """Resolve the absolute CHANGELOG-full.md path within the project root."""
    cfg = result.config.full_changelog
    return resolve_within_root(result.root, cfg.path, cfg.file)
