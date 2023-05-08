from datetime import datetime

from discord import SlashCommandGroup
from discord.ext import commands, tasks

from usagiBot.cogs.Twitch.twitch_utils import *
from usagiBot.db.models import UsagiTwitchNotify, UsagiConfig
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

from pycord18n.extension import _


class Twitch(commands.Cog):
    def __init__(self, bot):
        self.twitch = None
        self.bot = bot
        self.twitch_auth_loop.start()
        self.twitch_notify_loop.start()

    @tasks.loop(minutes=1, count=1)
    async def twitch_auth_loop(self):
        self.twitch = await twitch_auth()

    @twitch_auth_loop.before_loop
    async def before_twitch_auth_loop(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info(f"Logged in Twitch.")

    @tasks.loop(minutes=5)
    async def twitch_notify_loop(self):
        all_streams = await UsagiTwitchNotify.get_all()
        twitch_notify = {}

        for stream in all_streams:
            config = await UsagiConfig.get(
                guild_id=stream.guild_id, command_tag="twitch_notify"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            guild_notify = twitch_notify.setdefault(
                stream.guild_id, {"channel_to_notify": channel}
            )
            streamers_notify = guild_notify.setdefault("streamers", {})
            username_notify = streamers_notify.setdefault(
                stream.twitch_username,
                {"followers": [], "started_at": stream.started_at},
            )
            username_notify["followers"].append(stream.user_id)
            username_notify["started_at"] = max(
                username_notify["started_at"], stream.started_at
            )

        update_streamer = {}
        # {"streamer": {"start_at": "stream_start_at", "icon_url": "url"}}
        for guild_notify, data in twitch_notify.items():
            # go through every streamer on this guild and send a message
            channel = data["channel_to_notify"]
            for streamer, info in data["streamers"].items():
                stream = await first(self.twitch.get_streams(user_login=[streamer]))

                if stream is None:
                    continue
                if stream.started_at.replace(tzinfo=None) == info["started_at"]:
                    continue

                update_streamer.setdefault(
                    streamer,
                    {
                        "started_at": stream.started_at,
                        "icon_url": await get_streamer_icon(self.twitch, streamer),
                    },
                )
                followers = (
                    " ".join(list(map(lambda x: f"<@{x}>", info["followers"])))
                    + " <a:dinkDonk:865127621112102953>"
                )
                embed, image = get_notify_src(
                    stream, update_streamer[streamer]["icon_url"]
                )
                await channel.send(content=followers, embed=embed, file=image)

        for streamer, data in update_streamer.items():
            await UsagiTwitchNotify.update_all(
                {"twitch_username": streamer},
                {"started_at": data["started_at"].replace(tzinfo=None)},
            )

    @twitch_notify_loop.before_loop
    async def before_twitch_notify_loop(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info(f"Listen Twitch streamers.")

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    twitch_notify = SlashCommandGroup(
        name="twitch_notify",
        name_localizations={"ru": "твич_уведы"},
        description="Follow your favorite streamer and get notified when it goes live!",
        description_localizations={"ru": "Отслеживайте своих любимых стримеров прямо на сервере!."},
        command_tag="twitch_notify",
    )

    @twitch_notify.command(
        name="follow",
        name_localizations={"ru": "подписаться"},
        description="Follow streamer to notify.",
        description_localizations={"ru": "Подпишись чтобы получить уведомление о начале стрима."},
    )
    @discord.commands.option(
        name="streamer_name",
        name_localizations={"ru": "ник_стримера"},
        description="Streamer to follow.",
        description_localizations={"ru": "Ник стримера для подписки."},
    )
    async def follow_streamer(
        self,
        ctx,
        streamer_name: str,
    ) -> None:
        streamer_name = streamer_name.lower()
        user = await first(self.twitch.get_users(logins=[streamer_name]))
        if user is None:
            await ctx.respond(
                _("There isn't streamer with that nickname"), ephemeral=True
            )
            return
        streamer = await UsagiTwitchNotify.get(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            twitch_username=streamer_name,
        )
        if streamer is not None:
            await ctx.respond(
                _("You are already followed to this streamer"), ephemeral=True
            )
            return

        await UsagiTwitchNotify.create(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            twitch_username=streamer_name,
            started_at=datetime(year=2001, day=21, month=3).replace(tzinfo=None),
        )
        await ctx.respond(_("Followed you to streamer_name").format(streamer_name=streamer_name), ephemeral=True)

    @twitch_notify.command(
        name="unfollow",
        name_localizations={"ru": "отписаться"},
        description="Unfollow from streamer.",
        description_localizations={"ru": "Отписаться от стримера."},
    )
    @discord.commands.option(
        name="streamer_name",
        name_localizations={"ru": "ник_стримера"},
        description="Streamer to unfollow.",
        description_localizations={"ru": "Ник стримера для отписки."},
    )
    async def unfollow_streamer(
        self,
        ctx,
        streamer_name: str,
    ) -> None:
        streamer_name = streamer_name.lower()
        streamer = await UsagiTwitchNotify.get(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            twitch_username=streamer_name,
        )
        if streamer is None:
            await ctx.respond(_("You are not followed to this streamer"), ephemeral=True)
            return
        await UsagiTwitchNotify.delete(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            twitch_username=streamer_name,
        )
        await ctx.respond(_("Unfollowed you from streamer_name").format(streamer_name=streamer_name), ephemeral=True)

    @twitch_notify.command(
        name="show",
        name_localizations={"ru": "показать"},
        description="Show your follows.",
        description_localizations={"ru": "Показать все ваши подписки."},
    )
    async def show_user_follows(
        self,
        ctx,
    ) -> None:
        streamers = await UsagiTwitchNotify.get_all_by(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
        )
        if streamers is None:
            await ctx.respond(_("You are not followed to any streamer"), ephemeral=True)
            return
        streamers = list(map(lambda x: f" - {x.twitch_username}\n", streamers))
        streamers_list = _("Your followed streamers") + "".join(streamers)

        await ctx.respond(streamers_list, ephemeral=True)

    @twitch_notify.command(
        name="show_all",
        name_localizations={"ru": "показать_всех"},
        description="Show all streamers from guild.",
        description_localizations={"ru": "Показать все подписки на сервере."},
    )
    async def show_all_follows(
        self,
        ctx,
    ) -> None:
        streamers = await UsagiTwitchNotify.get_all_by(
            guild_id=ctx.guild.id,
        )
        if streamers is None:
            await ctx.respond(_("Your guild not followed to any streamer"), ephemeral=True)
            return
        streamers = list(set(map(lambda x: f" - {x.twitch_username}\n", streamers)))
        streamers_list = _("All streamers") + "\n".join(streamers)
        await ctx.respond(streamers_list, ephemeral=True)


def setup(bot):
    bot.add_cog(Twitch(bot))
