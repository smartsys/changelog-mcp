"""FastMCP-Setup und Registrierung aller 15 Tools.

stdout ist ausschließlich für MCP-JSON-RPC reserviert. Jede Log-Ausgabe geht über
das logging-Modul nach stderr (siehe __main__).
"""

from __future__ import annotations

from importlib.metadata import version as package_version
from typing import Literal

from mcp.server.fastmcp import FastMCP

from .store.models import Section
from .tools import add as add_tool
from .tools import config as config_tool
from .tools import edit as edit_tool
from .tools import import_ as import_tool
from .tools import init as init_tool
from .tools import release as release_tool
from .tools import render as render_tool
from .tools import search as search_tool
from .tools import version as version_tool
from .tools.import_ import ImportEntrySchema, ImportReleaseSchema

Bump = Literal["major", "minor", "patch"]
FormatName = Literal["keep-a-changelog", "conventional", "smart"]

mcp = FastMCP("changelog-mcp")
# FastMCP reicht keine Version an den Lowlevel-Server durch; ohne das Setzen meldet der
# Handshake die Version des mcp-SDK statt der Paketversion, weil
# create_initialization_options auf pkg_version("mcp") zurückfällt. Die Zahl kommt aus
# den Paket-Metadaten, damit pyproject.toml die einzige Pflegestelle bleibt.
mcp._mcp_server.version = package_version("changelog-mcp")


# -- Setup & Version ------------------------------------------------------
@mcp.tool()
def init_changelog(format: FormatName | None = None) -> str:
    """Legt leeren Store und Config-Datei an (Markdown entsteht beim ersten Release)."""
    return init_tool.init_changelog(fmt=format)


@mcp.tool()
def get_current_version() -> str:
    """Höchste Version im Store plus Anzahl unveröffentlichter Einträge."""
    return version_tool.get_current_version()


@mcp.tool()
def get_next_version(bump: Bump = "patch") -> str:
    """Berechnet die nächste Version aus der höchsten Store-Version und dem Modus."""
    return version_tool.get_next_version(bump=bump)


@mcp.tool()
def get_config() -> str:
    """Zeigt die aktive, aufgelöste Konfiguration als JSON inkl. Herkunft."""
    return config_tool.get_config()


# -- Laufende Erfassung ---------------------------------------------------
@mcp.tool()
def add_entry(
    category: str,
    description: str,
    details: list[str] | None = None,
    files: list[str] | None = None,
    bump: Bump = "patch",
    private: bool = False,
) -> str:
    """Hängt einen validierten Einzeleintrag an den Store an (append-only).

    private=true: Eintrag bleibt aus den publizierten Changelogs, solange das
    jeweilige includePrivate-Flag der Config nicht gesetzt ist.
    """
    return add_tool.add_entry(
        category=category,
        description=description,
        details=details,
        files=files,
        bump=bump,
        private=private,
    )


@mcp.tool()
def edit_entry(
    id: str,
    category: str | None = None,
    description: str | None = None,
    details: list[str] | None = None,
    files: list[str] | None = None,
) -> str:
    """Ändert Felder eines Eintrags per ID (nur genannte Felder, append-only)."""
    return edit_tool.edit_entry(
        id=id,
        category=category,
        description=description,
        details=details,
        files=files,
    )


@mcp.tool()
def delete_entry(id: str) -> str:
    """Löscht einen unveröffentlichten Eintrag per ID (append-only Tilgung)."""
    return edit_tool.delete_entry(id=id)


# -- Veröffentlichen ------------------------------------------------------
@mcp.tool()
def list_unreleased() -> str:
    """Zeigt alle Einträge seit dem letzten Release und die künftige Release-Version."""
    return release_tool.list_unreleased()


@mcp.tool()
def preview_release(summary: list[Section]) -> str:
    """Rendert den Release-Block wie create_release, ohne zu schreiben."""
    return release_tool.preview_release(summary=summary)


@mcp.tool()
def create_release(summary: list[Section] | None = None) -> str:
    """Bündelt unveröffentlichte Einträge zu einem Release und rendert beide Dateien.

    summary beschreibt nur den öffentlichen Block. Bei einem reinen Privat-Release
    (alle offenen Einträge privat, includePrivate=false) darf summary leer bleiben.
    """
    return release_tool.create_release(summary=summary)


# -- Suche & Abruf --------------------------------------------------------
@mcp.tool()
def search_entries(
    query: str | None = None,
    category: str | None = None,
    file: str | None = None,
    version: str | None = None,
    released: bool | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    limit: int = 10,
) -> str:
    """Durchsucht den strukturierten Store (Ranking, alle Filter UND-kombiniert)."""
    return search_tool.search_entries(
        query=query,
        category=category,
        file=file,
        version=version,
        released=released,
        dateFrom=dateFrom,
        dateTo=dateTo,
        limit=limit,
    )


@mcp.tool()
def get_release(version: str) -> str:
    """Zeigt einen Release mit Zusammenfassung und allen gebündelten Einträgen."""
    return search_tool.get_release(version=version)


# -- Rendern & Migration --------------------------------------------------
@mcp.tool()
def render_changelog() -> str:
    """Erzeugt beide Markdown-Dateien neu aus dem Store (idempotent, Render-Schutz)."""
    return render_tool.render_changelog()


@mcp.tool()
def import_records(
    entries: list[ImportEntrySchema],
    releases: list[ImportReleaseSchema] | None = None,
) -> str:
    """Migration: hängt geparste Einträge (und optional Releases) an den Store an."""
    return import_tool.import_records(entries=entries, releases=releases)


@mcp.tool()
def verify_store(sourceFile: str) -> str:
    """Vergleicht Versions-Headings der Quelldatei mit dem Store und meldet
    Fehlendes."""
    return import_tool.verify_store(sourceFile=sourceFile)
