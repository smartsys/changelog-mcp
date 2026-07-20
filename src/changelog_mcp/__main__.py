"""Entry Point: startet den MCP-Server über stdio.

Logging geht ausschließlich nach stderr, damit stdout dem MCP-JSON-RPC-Protokoll
vorbehalten bleibt.
"""

from __future__ import annotations

import logging
import sys


def main() -> None:
    """Start the changelog-mcp server over stdio."""
    # Logging nach stderr konfigurieren — niemals auf stdout schreiben.
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Import erst hier, damit ein reiner Modul-Import keine Nebenwirkungen hat.
    from .server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
