"""Resolve a user link (YouTube video/playlist/search or direct audio URL) into queue entries."""
import asyncio
import functools
import logging
from dataclasses import dataclass
from typing import Any, Callable

from usagiBot.cogs.Music.music_utils import get_audio_duration
from usagiBot.cogs.Music.seek import is_youtube_domain, link_domain
from usagiBot.cogs.Music.sources import YTDLSource, error_messages
from usagiBot.src.UsagiNet import UnsafeUrlError, validate_public_http_url

logger = logging.getLogger(__name__)

UNSUPPORTED_AUDIO = "Unable to add this song, maybe it is not an audio file?"
PRIVATE_ADDRESS = "That link points to a private or local address"


@dataclass(frozen=True)
class EnqueueResult:
    ok: bool
    message: str


def _not_found(link: str) -> EnqueueResult:
    return EnqueueResult(False, f"Couldn't find anything that matches `{link}`")


async def _is_public(url: str) -> bool:
    try:
        await validate_public_http_url(url)
    except UnsafeUrlError as e:
        logger.warning("Refused music link %r: %s", url, e)
        return False
    return True


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
    loop: asyncio.AbstractEventLoop,
    state: Any,
    link: str,
    requester: Any,
    query: str | None = None,
) -> EnqueueResult:
    try:
        data = await _extract(loop, YTDLSource.ytdl.extract_info, query or link)
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
    # yt-dlp's generic extractor and ffmpeg fetch whatever they are given,
    # so both the link and the stream it resolves to must be public hosts
    if not await _is_public(link):
        return EnqueueResult(False, PRIVATE_ADDRESS)
    try:
        data = _first_entry(await _extract(loop, YTDLSource.ytdl.extract_info, link))
        if data is None:
            return _not_found(link)
        stream_url = data["url"]
        if "duration" in data:
            duration = int(float(data["duration"]))
        else:
            duration = await get_audio_duration(link)
        title = data["title"]
    except Exception as e:
        logger.error("Couldn't enqueue direct link %r: %s", link, e)
        return EnqueueResult(False, UNSUPPORTED_AUDIO)
    if not await _is_public(stream_url):
        return EnqueueResult(False, PRIVATE_ADDRESS)
    await state.songs.put(
        {
            "url": link,
            "title": title,
            "user": requester,
            "duration": duration,
            "realurl": stream_url,
        }
    )
    return EnqueueResult(True, "Enqueued **{0}**".format(title.replace("_", "\\_")))


async def enqueue_link(
    loop: asyncio.AbstractEventLoop, state: Any, link: str, requester: Any
) -> EnqueueResult:
    """
    Add whatever `link` points to onto `state.songs`. Text that isn't a URL
    is searched on YouTube explicitly: yt-dlp's default_search=auto would
    otherwise turn "host/path" text into an unchecked http:// fetch.
    """
    domain = link_domain(link)
    if domain is None:
        result = await _enqueue_youtube(
            loop, state, link, requester, query=f"ytsearch:{link}"
        )
    elif is_youtube_domain(domain):
        if "/playlist?" in link:
            result = await _enqueue_playlist(loop, state, link, requester)
        else:
            result = await _enqueue_youtube(loop, state, link, requester)
    else:
        result = await _enqueue_direct(loop, state, link, requester)

    if result.ok:
        state.stopped = False
    return result
