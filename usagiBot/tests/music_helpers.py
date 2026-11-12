"""Shared fakes for the Music cog tests.

The real VoiceState starts an audio-player task and talks to Discord voice,
so command and view tests drive a MagicMock state that carries a real
SongQueue — queue behaviour is what most commands actually touch.
"""
from typing import Any, Optional
from unittest import mock

YOUTUBE_URL = "https://www.youtube.com/watch?v=abc"


def make_bot() -> mock.MagicMock:
    bot = mock.MagicMock()
    bot.user.id = 999

    async def run_in_executor(_executor: Any, fn: Any) -> Any:
        return fn()

    bot.loop.run_in_executor = mock.AsyncMock(side_effect=run_in_executor)

    def create_task(coro: Any) -> mock.MagicMock:
        # Never schedule the real coroutine: close it so it isn't reported
        # as "never awaited", and hand back a task-shaped mock.
        coro.close()
        task = mock.MagicMock()
        task.done.return_value = False
        return task

    bot.loop.create_task = mock.MagicMock(side_effect=create_task)
    return bot


def make_current(
    title: str = "song",
    url: str = YOUTUBE_URL,
    duration: int = 200,
    start_time: float = 1000.0,
) -> mock.MagicMock:
    current = mock.MagicMock()
    current.source.title = title
    current.source.url = url
    current.source.duration_int = duration
    current.source.requester = mock.MagicMock(name="requester")
    current.start_time = start_time
    current.pause_duration = 0
    current.pause_time = 0
    current.paused = False
    return current


def make_state(voice_channel: Any, current: Optional[Any] = None) -> mock.MagicMock:
    from usagiBot.cogs.Music.sources import SongQueue

    state = mock.MagicMock()
    state.songs = SongQueue()
    state.voice.channel = voice_channel
    state.voice.is_playing.return_value = True
    state.voice.is_paused.return_value = False
    state.voice.move_to = mock.AsyncMock()
    state.current = current
    state.is_playing = current is not None
    state.loop = False
    state.loop_queue = False
    state.stop = mock.AsyncMock()
    state.seek = mock.AsyncMock()
    return state


def make_ctx(current: Optional[Any] = None) -> mock.MagicMock:
    """Slash-command ctx whose author sits in the bot's voice channel."""
    ctx = mock.MagicMock()
    for name in ("respond", "defer", "send_followup", "edit", "delete"):
        setattr(ctx, name, mock.AsyncMock())
    ctx.me.edit = mock.AsyncMock()
    ctx.guild.id = 42
    ctx.interaction.response.is_done.return_value = False

    voice_channel = mock.MagicMock(name="voice_channel")
    voice_channel.connect = mock.AsyncMock()
    voice_channel.permissions_for.return_value.connect = True
    ctx.author.voice.channel = voice_channel
    ctx.author.guild_permissions.move_members = True
    ctx.voice_client = None
    ctx.from_play = False
    ctx.debug = {"debug": False}
    ctx.voice_state = make_state(voice_channel, current)
    return ctx


def make_interaction(user: Any = None) -> mock.MagicMock:
    interaction = mock.MagicMock()
    interaction.user = user if user is not None else mock.MagicMock(name="user")
    interaction.response.defer = mock.AsyncMock()
    interaction.response.send_message = mock.AsyncMock()
    interaction.response.edit_message = mock.AsyncMock()
    interaction.edit_original_response = mock.AsyncMock()
    interaction.original_response = mock.AsyncMock(return_value=mock.MagicMock(id=7))
    interaction.followup.send = mock.AsyncMock()
    interaction.followup.edit_message = mock.AsyncMock()
    sent = mock.MagicMock()
    sent.edit = mock.AsyncMock()
    sent.delete = mock.AsyncMock()
    interaction.channel.send = mock.AsyncMock(return_value=sent)
    return interaction


def embed_title(async_mock: mock.AsyncMock) -> str:
    """Title of the embed passed to the most recent call."""
    return async_mock.call_args.kwargs["embed"].title


def embed_titles(async_mock: mock.AsyncMock) -> list:
    return [
        call.kwargs["embed"].title
        for call in async_mock.call_args_list
        if "embed" in call.kwargs
    ]
