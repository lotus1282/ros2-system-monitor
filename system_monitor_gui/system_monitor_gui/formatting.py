"""Small, dependency-free formatting helpers used by the Qt dashboard."""

from __future__ import annotations

from datetime import datetime

_UNITS = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")


def human_bytes(value: float | int | None, precision: int = 1) -> str:
    """Return a compact binary byte string, e.g. ``1.5 GiB``."""
    if value is None:
        return "n/a"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if number < 0:
        return "n/a"
    unit = _UNITS[0]
    for candidate in _UNITS:
        unit = candidate
        if number < 1024.0 or candidate == _UNITS[-1]:
            break
        number /= 1024.0
    if unit == "B":
        return f"{int(number)} B"
    return f"{number:.{precision}f} {unit}"


def human_rate(value: float | int | None) -> str:
    """Return a byte-per-second string, e.g. ``2.4 MiB/s``."""
    formatted = human_bytes(value)
    return "n/a" if formatted == "n/a" else f"{formatted}/s"


def format_stamp(sec: int, nanosec: int = 0) -> str:
    """Format a ROS time pair as local wall-clock time."""
    try:
        timestamp = float(sec) + float(nanosec) / 1_000_000_000.0
        return datetime.fromtimestamp(timestamp).astimezone().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (TypeError, ValueError, OSError, OverflowError):
        return "n/a"
