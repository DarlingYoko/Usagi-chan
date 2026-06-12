import asyncio
import functools
import logging
import time

import discord

from usagiBot.cogs.Music.music_utils import (
    check_user_in_voice_interaction,
    create_music_embed,
    get_children_by_id,
    join_voice_channel,
    parse_songs,
    set_loop_btns,
)
from usagiBot.cogs.Music.sources import YTDLError, YTDLSource, error_messages
from usagiBot.src.UsagiUtils import get_embed

logger = logging.getLogger(__name__)


class SearchMenu(discord.ui.Select):
    def __init__(self, bot, options_raw, cog, ctx):
        self.bot = bot
        self.cog = cog
        self.ctx = ctx
        reaction_list = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
        ]
        options = [
            discord.SelectOption(
                label=data["title"],
                description=f"Duration: {data['duration']}",
                value=str(data["index"]),
                emoji=reaction_list[data["index"]],
            )
            for data in options_raw
        ]
        options.append(
            discord.SelectOption(
                label="Cancel",
                description="Cancel the search",
                value="11",
                emoji="❌",
            )
        )
        self.data = options_raw
        self.completed = False
        super().__init__(
            placeholder="Select the desired song...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        if int(self.values[0]) == 11:
            self.completed = True
            return await interaction.response.edit_message(
                embed=get_embed(
                    title="Cancelled",
                    description=None,
                    color=discord.Color.green(),
                ),
                view=None,
            )
        # Edit the message to reduce its size
        await interaction.response.edit_message(
            embed=get_embed(
                title="Selected:",
                description=self.data[int(self.values[0])]["title"],
                color=discord.Color.green(),
            ),
            view=None,
        )
        msg = await interaction.original_response()

        # Invoke the play command

        if not self.ctx.author.voice or not self.ctx.author.voice.channel:
            return await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title="You are not connected to any voice channel or the same voice channel.",
                    color=discord.Color.red(),
                ),
            )
        guild = self.bot.get_guild(interaction.guild_id) or await self.bot.fetch_guild(
            interaction.guild_id
        )
        voice_client = guild.voice_client
        if voice_client:
            if voice_client.channel != self.ctx.author.voice.channel:
                return await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title="Bot is already in a voice channel.",
                        color=discord.Color.red(),
                    ),
                )

        ctx = self.ctx
        search = self.data[int(self.values[0])]["url"]
        if search is None:
            return await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title="Bot is already in a voice channel.",
                    color=discord.Color.red(),
                ),
            )
        # Joins the channel if it hasn't
        if not ctx.voice_state.voice:
            ctx.from_play = True
            await join_voice_channel(ctx)
        # Errors may occur while joining the channel, if the voice is None, don't continue
        if not ctx.voice_state.voice:
            return
        if not ctx.debug["debug"]:
            # If the user invoking this command is not in the same channel, return error
            if (
                not ctx.author.voice
                or not ctx.author.voice.channel
                or (
                    ctx.voice_state.voice
                    and ctx.author.voice.channel != ctx.voice_state.voice.channel
                )
            ):
                return await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title="You are not connected to any voice channel or the same voice channel.",
                        color=discord.Color.red(),
                    ),
                )

            if ctx.voice_client:
                if ctx.voice_client.channel != ctx.author.voice.channel:
                    return await interaction.followup.edit_message(
                        message_id=msg.id,
                        embed=get_embed(
                            title="Bot is already in a voice channel.",
                            color=discord.Color.red(),
                        ),
                    )

        loop = self.bot.loop
        try:
            await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title=f"Searching for: **<{search}>**",
                    color=discord.Color.green(),
                ),
            )
            # Supports playing a playlist but it must be like https://youtube.com/playlist?
            if "/playlist?" in search:
                partial = functools.partial(
                    YTDLSource.ytdl_playlist.extract_info, search, download=False
                )
                data = await loop.run_in_executor(None, partial)
                if data is None:
                    return await interaction.followup.edit_message(
                        message_id=msg.id,
                        embed=get_embed(
                            title=f"Couldn't find anything that matches `{search}`",
                            color=discord.Color.red(),
                        ),
                    )
                playlist = await parse_songs(ctx, data)
                await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title=f"Enqueued **{len(playlist)}** songs",
                        color=discord.Color.green(),
                    ),
                )
            else:
                # Just a single song
                try:
                    partial = functools.partial(
                        YTDLSource.ytdl.extract_info, search, download=False
                    )
                    data = await loop.run_in_executor(None, partial)
                except Exception as e:
                    # Get the error message from the dictionary, if it doesn't exist in dict, return the original error
                    # message
                    message = error_messages.get(str(e), str(e))
                    return await interaction.followup.edit_message(
                        message_id=msg.id,
                        embed=get_embed(
                            title=f"Error: {message}",
                            color=discord.Color.red(),
                        ),
                    )
                if "entries" in data:
                    if len(data["entries"]) > 0:
                        data = data["entries"][0]
                    else:
                        return await interaction.followup.edit_message(
                            message_id=msg.id,
                            embed=get_embed(
                                title=f"Couldn't find anything that matches `{search}`",
                                color=discord.Color.red(),
                            ),
                        )
                # Add the song to the pending list
                try:
                    duration = int(data["duration"])
                except Exception as e:
                    logger.error("Couldn't parse search result duration: %s", e)
                    duration = 0
                await ctx.voice_state.songs.put(
                    {
                        "url": data["webpage_url"],
                        "title": data["title"],
                        "user": ctx.author,
                        "duration": duration,
                    }
                )
                await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title=f"Enqueued **{data['title']}**",
                        color=discord.Color.green(),
                    ),
                )
            ctx.voice_state.stopped = False
        except YTDLError as e:
            await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title=f"Error: {str(e)}",
                    color=discord.Color.red(),
                ),
            )
        self.completed = True


class SearchView(discord.ui.View):
    def __init__(self, bot, data, ctx, cog):
        self.bot = bot
        self.ctx = ctx
        self.data = data
        self.cog = cog
        super().__init__(timeout=60)
        self.add_item(SearchMenu(self.bot, data, cog, ctx))

    async def on_timeout(self):
        if not self.children[0].completed:
            await self.message.edit(
                embed=get_embed(title="Timed out", color=0xFF0000),
                view=None,
            )


class SkipVoteView(discord.ui.View):
    def __init__(self, bot, voice_state, voting):
        self.bot = bot
        self.voice_state = voice_state
        self.voting = voting
        self.votes = 1
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="<:greenTick:874767321007276143>",
    )
    async def yes_btn(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        if interaction.user in self.voting["agree"]:
            return await interaction.followup.send(
                embed=get_embed(
                    title="You already voted for skip.", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if interaction.user in self.voting["disagree"]:
            self.voting["disagree"].remove(interaction.user)

        self.voting["agree"].append(interaction.user)
        self.votes += 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to agree", color=discord.Color.green()),
            ephemeral=True,
        )

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="<:redThick:874767320915005471>",
    )
    async def no_btn(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        if interaction.user in self.voting["disagree"]:
            return await interaction.followup.send(
                embed=get_embed(
                    title="You already voted against skip.", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        if interaction.user in self.voting["agree"]:
            self.voting["agree"].remove(interaction.user)

        self.voting["disagree"].append(interaction.user)
        self.votes -= 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to disagree", color=discord.Color.green()),
            ephemeral=True,
        )


class StopVoteView(discord.ui.View):
    def __init__(self, bot, voice_state, voting):
        self.bot = bot
        self.voice_state = voice_state
        self.voting = voting
        self.votes = 1
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="<:greenTick:874767321007276143>",
    )
    async def yes_btn(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        if interaction.user in self.voting["agree"]:
            return await interaction.followup.send(
                embed=get_embed(
                    title="You already voted for stop.", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if interaction.user in self.voting["disagree"]:
            self.voting["disagree"].remove(interaction.user)

        self.voting["agree"].append(interaction.user)
        self.votes += 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Stop current queue?",
                description=f"Votes to stop - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to agree", color=discord.Color.green()),
            ephemeral=True,
        )

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="<:redThick:874767320915005471>",
    )
    async def no_btn(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        if interaction.user in self.voting["disagree"]:
            return await interaction.followup.send(
                embed=get_embed(
                    title="You already voted against stop.", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        if interaction.user in self.voting["agree"]:
            self.voting["agree"].remove(interaction.user)

        self.voting["disagree"].append(interaction.user)
        self.votes -= 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Stop current queue?",
                description=f"Votes to stop - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to disagree", color=discord.Color.green()),
            ephemeral=True,
        )


class PlayerControlView(discord.ui.View):
    def __init__(self, bot, voice_state):
        self.bot = bot
        self.voice_state = voice_state
        super().__init__(timeout=None)
        set_loop_btns(self)

    @discord.ui.button(
        label="Pause",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="0",
        emoji="⏸",
        disabled=False,
    )
    async def pause(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()
        if self.voice_state.is_playing and self.voice_state.voice.is_playing():
            self.voice_state.voice.pause()
            # Sets the pause time
            self.voice_state.current.pause_time = time.time()
            self.voice_state.current.paused = True
            get_children_by_id(self.children, "0").emoji = "▶"
            get_children_by_id(self.children, "0").label = "Resume"
        elif self.voice_state.is_playing and self.voice_state.voice.is_paused():
            self.voice_state.voice.resume()
            # Updates internal data for handling song progress that was paused
            self.voice_state.current.pause_duration += (
                time.time() - self.voice_state.current.pause_time
            )
            self.voice_state.current.pause_time = 0
            self.voice_state.current.paused = False
            get_children_by_id(self.children, "0").emoji = "⏸"
            get_children_by_id(self.children, "0").label = "Pause"
        await interaction.edit_original_response(view=self)

    @discord.ui.button(
        label="Skip",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="1",
        emoji="⏭",
        disabled=False,
    )
    async def skip(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        vote_view = SkipVoteView(
            self.bot,
            self.voice_state,
            {"agree": [interaction.user], "disagree": []},
        )
        msg = await interaction.channel.send(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await msg.edit(
                embed=get_embed(title="Skip approved", color=discord.Color.green()),
                view=None,
            )
            self.voice_state.skip()
            await asyncio.sleep(3)
        else:
            await msg.edit(
                embed=get_embed(title="Skip canceled", color=discord.Color.red()),
                view=None,
            )
        await msg.delete(delay=10)

    @discord.ui.button(
        label="Stop",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="2",
        emoji="⏹",
        disabled=False,
    )
    async def stop(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        vote_view = StopVoteView(
            self.bot,
            self.voice_state,
            {"agree": [interaction.user], "disagree": []},
        )
        msg = await interaction.channel.send(
            embed=get_embed(
                title="Stop current queue?",
                description="Votes to stop - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await msg.edit(
                embed=get_embed(title="Stop approved", color=discord.Color.green()),
                view=None,
            )
            self.voice_state.songs.clear()

            if self.voice_state.is_playing:
                await self.voice_state.stop()
                self.voice_state.stopped = True
        else:
            await msg.edit(
                embed=get_embed(title="Stop canceled", color=discord.Color.red()),
                view=None,
            )
        await msg.delete(delay=10)

    @discord.ui.button(
        label="Loop",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="3",
        emoji="🔂",
        disabled=False,
    )
    async def loop(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()
        self.voice_state.loop = not self.voice_state.loop
        set_loop_btns(self)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(
        label="Queue",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="5",
        emoji="📜",
        disabled=False,
    )
    async def queue(self, button, interaction):
        # Shows the queue, add page number to view different pages
        page = 1
        if len(self.voice_state.songs) == 0 and self.voice_state.current is None:
            return await interaction.response.send_message(
                embed=get_embed(title="Empty queue.", color=discord.Color.red()),
                ephemeral=True,
            )

        # Invoking queue while the bot is retrieving another song will cause error, wait for 1 second
        while self.voice_state.current is None or isinstance(
            self.voice_state.current, dict
        ):
            await asyncio.sleep(1)
        return await interaction.response.send_message(
            embed=create_music_embed(self, page),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Loop Queue",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="4",
        emoji="🔂",
        disabled=False,
    )
    async def loopqueue(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()
        self.voice_state.loop_queue = not self.voice_state.loop_queue
        try:
            if self.voice_state.loop_queue:
                await self.voice_state.songs.put(
                    {
                        "url": self.voice_state.current.source.url,
                        "title": self.voice_state.current.source.title,
                        "user": self.voice_state.current.source.requester,
                        "duration": self.voice_state.current.source.duration_int,
                    }
                )
        except AttributeError:
            pass
        set_loop_btns(self)
        await interaction.edit_original_response(view=self)
