"""Resolve a user link (YouTube video/playlist/search or direct audio URL) into queue entries."""
import asyncio
import functools
import logging
from dataclasses import dataclass
from typing import Any, Callable

from usagiBot.cogs.Music.music_utils import get_audio_duration
from usagiBot.cogs.Music.seek import is_youtube_domain, link_domain
from usagiBot.cogs.Music.sources import YTDLSource, error_messages

logger = logging.getLogger(__name__)

UNSUPPORTED_AUDIO = "Unable to add this song, maybe it is not an audio file?"


@dataclass(frozen=True)
class EnqueueResult:
    ok: bool
    message: str


def _not_found(link: str) -> EnqueueResult:
    return EnqueueResult(False, f"Couldn't find anything that matches `{link}`")


async def _extract(
    loop: asyncio.AbstractEventLoop, extractor: Callable[..., Any], link: str
) -> Any:
    # yt-dlp is blocking — never run it on the event loop
    return await loop.run_in_executor(
        None, functools.partial(extractor, link, download=False)
    )


def _first_entry(data: dict) -> Any:
    """The video itself, or the first search hit; None when the search is empty."""
    if "entries" not in data:
        return data
    return data["entries"][0] if data["entries"] else None


async def _enqueue_playlist(
    loop: asyncio.AbstractEventLoop, state: Any, link: str, requester: Any
) -> EnqueueResult:
    data = await _extract(loop, YTDLSource.ytdl_playlist.extract_info, link)
    if data is None:
        return _not_found(link)
    # flat playlist entries are YouTube ids; entries without a duration are
    # unavailable/private videos
    songs = [
        {
            "url": "https://youtu.be/" + entry["id"],
            "title": entry["title"],
            "user": requester,
            "duration": int(entry["duration"]),
        }
        for entry in data["entries"]
        if entry["duration"] is not None
    ]
    for song in songs:
        await state.songs.put(song)
    return EnqueueResult(True, f"Enqueued **{len(songs)}** songs")


async def _enqueue_youtube(
    loop: asyncio.AbstractEventLoop, state: Any, link: str, requester: Any
) -> EnqueueResult:
    try:
        data = await _extract(loop, YTDLSource.ytdl.extract_info, link)
    except Exception as e:
        return EnqueueResult(False, f"Error: {error_messages.get(str(e), str(e))}")
    data = _first_entry(data)
    if data is None:
        return _not_found(link)
    try:
        duration = int(data["duration"])
    except (KeyError, TypeError, ValueError) as e:
        logger.error("Couldn't parse duration: %s", e)
        duration = 0
    await state.songs.put(
        {
            "url": data["webpage_url"],
            "title": data["title"],
            "user": requester,
            "duration": duration,
        }
    )
    return EnqueueResult(True, f"Enqueued **{data['title']}**")


async def _enqueue_direct(
    loop: asyncio.AbstractEventLoop, state: Any, link: str, requester: Any
) -> EnqueueResult:
    try:
        data = _first_entry(await _extract(loop, YTDLSource.ytdl.extract_info, link))
        if data is None:
            return _not_found(link)
        if "duration" in data:
            duration = int(float(data["duration"]))
        else:
            duration = await get_audio_duration(link)
        title = data["title"]
        await state.songs.put(
            {
                "url": link,
                "title": title,
                "user": requester,
                "duration": duration,
                "realurl": data["url"],
            }
        )
    except Exception as e:
        logger.error("Couldn't enqueue direct link %r: %s", link, e)
        return EnqueueResult(False, UNSUPPORTED_AUDIO)
    return EnqueueResult(True, "Enqueued **{0}**".format(title.replace("_", "\\_")))


async def enqueue_link(
    loop: asyncio.AbstractEventLoop, state: Any, link: str, requester: Any
) -> EnqueueResult:
    """
    Add whatever `link` points to onto `state.songs`. Text that isn't a URL
    is handed to YouTube search (yt-dlp default_search).
    """
    domain = link_domain(link)
    if domain is None or is_youtube_domain(domain):
        if domain is not None and "/playlist?" in link:
            result = await _enqueue_playlist(loop, state, link, requester)
        else:
            result = await _enqueue_youtube(loop, state, link, requester)
    else:
        result = await _enqueue_direct(loop, state, link, requester)

    if result.ok:
        state.stopped = False
    return result
