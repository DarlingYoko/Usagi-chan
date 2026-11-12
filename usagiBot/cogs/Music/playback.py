"""Player actions shared by slash commands and the now-playing buttons."""
import time
from typing import Any


def pause_song(state: Any) -> bool:
    """Pause the current song; False when nothing is playing."""
    if not (state.is_playing and state.voice.is_playing()):
        return False
    state.voice.pause()
    state.current.pause_time = time.time()
    state.current.paused = True
    return True


def resume_song(state: Any) -> bool:
    """Resume a paused song; False when nothing is paused."""
    if not (state.is_playing and state.voice.is_paused()):
        return False
    state.voice.resume()
    current = state.current
    current.pause_duration += time.time() - current.pause_time
    current.pause_time = 0
    current.paused = False
    return True


async def stop_queue(state: Any) -> bool:
    """Drop the queue and stop the player; True when a song was interrupted."""
    state.songs.clear()
    if not state.is_playing:
        return False
    await state.stop()
    state.stopped = True
    return True


async def requeue_current(state: Any) -> None:
    """Put the current song at the end of the queue (loop-queue mode)."""
    source = getattr(state.current, "source", None)
    if source is None:
        return
    await state.songs.put(
        {
            "url": source.url,
            "title": source.title,
            "user": source.requester,
            "duration": source.duration_int,
        }
    )


async def toggle_loop_queue(state: Any) -> bool:
    """Flip loop-queue mode; enabling it also queues the current song again."""
    state.loop_queue = not state.loop_queue
    if state.loop_queue:
        await requeue_current(state)
    return state.loop_queue
