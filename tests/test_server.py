"""Server-Registrierung: alle 15 Tools sind vorhanden, kein stdout beim Import."""

from __future__ import annotations

import asyncio
import io
from contextlib import redirect_stdout

EXPECTED_TOOLS = {
    "init_changelog",
    "get_current_version",
    "get_next_version",
    "get_config",
    "add_entry",
    "edit_entry",
    "delete_entry",
    "list_unreleased",
    "preview_release",
    "create_release",
    "search_entries",
    "get_release",
    "render_changelog",
    "import_records",
    "verify_store",
}


def test_import_produces_no_stdout() -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        import importlib

        import changelog_mcp.server as server

        importlib.reload(server)
    assert buffer.getvalue() == ""


def test_all_15_tools_registered() -> None:
    from changelog_mcp.server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS
    assert len(names) == 15


def test_handshake_reports_package_version() -> None:
    """Der Handshake muss die Paketversion melden, nicht die des mcp-SDK."""
    from importlib.metadata import version

    from changelog_mcp.server import mcp

    options = mcp._mcp_server.create_initialization_options()
    expected = version("changelog-mcp")
    assert options.server_version == expected
    assert options.server_version != version("mcp")
