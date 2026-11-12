"""Parsing of the /music seek argument."""
import re
from typing import Any, Optional, Tuple

# "1h2m3s", "2m", "45s" — every unit optional, but at least one must be present
_CLOCK = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def link_domain(url: str) -> Optional[str]:
    """Host part of "scheme://host/..." or None when the text isn't a URL."""
    parts = url.split("/")
    return parts[2] if len(parts) > 2 else None


def is_youtube_domain(domain: Optional[str]) -> bool:
    return domain is not None and ("youtube" in domain or "youtu.be" in domain)


def elapsed_seconds(song: Any, now: float) -> int:
    """
    Playback position of `song`, excluding time spent paused. An open pause
    is folded into pause_duration so the next call doesn't count it twice.
    """
    if song.paused:
        song.pause_duration += now - song.pause_time
        song.pause_time = now
    return int(now - song.start_time - song.pause_duration)


def parse_seek_target(raw: str, song: Any, now: float) -> int:
    """
    Absolute target second for a seek request: "90", "1h2m3s", or a relative
    "+15" / "-15" from the current position. Raises ValueError on anything else.
    """
    raw = raw.strip()
    if raw[:1] in ("+", "-"):
        offset = raw[1:]
        if not offset.isdigit():
            raise ValueError(f"bad relative seek {raw!r}")
        position = elapsed_seconds(song, now)
        if raw[0] == "+":
            return position + int(offset)
        return max(position - int(offset), 0)

    if raw.isdigit():
        return int(raw)

    match = _CLOCK.fullmatch(raw)
    if not match or not any(match.groups()):
        raise ValueError(f"bad seek {raw!r}")
    hours, minutes, seconds = (int(group or 0) for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def source_kind(url: str) -> Tuple[bool, bool]:
    """(is_local_file, is_direct_link) — how VoiceState.seek must rebuild the source."""
    return "local@" in url, not is_youtube_domain(link_domain(url))
