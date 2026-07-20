"""Date formatting with the config tokens YYYY / MM / DD."""

from __future__ import annotations

from datetime import UTC, datetime

# Reihenfolge wichtig: längere Tokens zuerst ersetzen (YYYY vor YY existiert nicht,
# aber MM/DD sind eindeutig). strftime-Codes werden erst am Ende angewendet.
_TOKEN_MAP = (
    ("YYYY", "%Y"),
    ("MM", "%m"),
    ("DD", "%d"),
)


def format_date(dt: datetime, date_format: str) -> str:
    """Format a datetime using the config tokens (YYYY, MM, DD).

    Example: date_format 'DD.MM.YYYY' -> '19.07.2026'.
    """
    strftime_fmt = date_format
    for token, code in _TOKEN_MAP:
        strftime_fmt = strftime_fmt.replace(token, code)
    return dt.strftime(strftime_fmt)


def today_str(date_format: str) -> str:
    """Return today's date (UTC) formatted with the given tokens."""
    return format_date(datetime.now(UTC), date_format)


def now_ts() -> str:
    """Return the current UTC timestamp as ISO string with millis and 'Z'."""
    ts = datetime.now(UTC).isoformat(timespec="milliseconds")
    # '+00:00' durch 'Z' ersetzen für kompakte ISO-Notation.
    return ts.replace("+00:00", "Z")
