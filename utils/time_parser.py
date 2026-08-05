"""
Time parser utility for converting human readable time durations (e.g. 30s, 5m, 2h, 1d, 3w)
into seconds or timedelta objects.
"""

import re
from datetime import timedelta
from typing import Optional

TIME_REGEX = re.compile(r"^(?:(\d+)\s*d)?\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?$", re.IGNORECASE)

SINGLE_REGEX = re.compile(r"(\d+)\s*([s|m|h|d|w])", re.IGNORECASE)

TIME_UNITS = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800
}


def parse_duration(time_str: str) -> Optional[int]:
    """
    Parses a time string like '30s', '5m', '2h', '1d', '3w' or '2h30m' into total seconds.
    Returns total seconds as int, or None if invalid format.
    """
    if not time_str:
        return None

    # Try matching concatenated units like 1d2h or single unit like 5m
    matches = SINGLE_REGEX.findall(time_str)
    if not matches:
        return None

    total_seconds = 0
    for value, unit in matches:
        unit_lower = unit.lower()
        if unit_lower in TIME_UNITS:
            total_seconds += int(value) * TIME_UNITS[unit_lower]

    return total_seconds if total_seconds > 0 else None


def format_duration(seconds: int) -> str:
    """Format total seconds into human-readable string like '2 hours, 30 minutes'."""
    if seconds <= 0:
        return "Expired"

    weeks, seconds = divmod(seconds, 604800)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if weeks > 0:
        parts.append(f"{int(weeks)}w")
    if days > 0:
        parts.append(f"{int(days)}d")
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if seconds > 0 or not parts:
        parts.append(f"{int(seconds)}s")

    return " ".join(parts)
