import discord
from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from discord.ext import commands
from discord.ext.commands import BadColourArgument
from usagiBot.src.UsagiErrors import (
    UsagiNotSetUpError,
    UsagiModuleDisabledError,
    UsagiCallFromNotModerError,
    UsagiCallFromWrongChannelError,
)
from usagiBot.tests.utils import *


class TestEventsMethods(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiBackup", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_UsagiBackup) -> None:
        self.ctx = mock.AsyncMock()
        self.bot = mock.MagicMock()

        from usagiBot.cogs.Events.index import Events

        self.ctx.author.name = "Yoko"
        self.Events = Events(self.bot)

        self.bot.i18n = init_i18n()
        self.bot.language = {}

    async def test_command_not_found(self) -> None:
        await self.Events.on_command_error(self.ctx, commands.CommandNotFound())
        self.ctx.reply.assert_called_with(
            "This command doesn't exist.", delete_after=120
        )

    async def test_command_on_cooldown(self) -> None:
        error = commands.CommandOnCooldown(
            cooldown=commands.Cooldown(rate=1, per=60.0),
            retry_after=60.0,
            type=commands.BucketType.user,
        )
        await self.Events.on_command_error(self.ctx, error)
        self.ctx.reply.assert_called_with(
            "You can use this command in 60s", delete_after=120
        )

    async def test_on_command_error(self) -> None:
        user = mock.AsyncMock()
        self.ctx.bot.get_user = mock.MagicMock(return_value=None)
        self.ctx.bot.fetch_user.return_value = user
        self.ctx.command.name = "test_command_name"
        self.ctx.author.mention = "test_author_mention"
        self.ctx.message.id = "test_message"
        self.ctx.channel.id = "test_channel"
        self.ctx.args = "test_args"
        self.ctx.kwargs = "test_kwargs"

        self.error = mock.MagicMock()
        self.error.__str__.return_value = "test_error_message"

        test_error_message = (
            "**NEW ERROR OCCURRED**\n"
            + "> **Command** - test_command_name\n"
            + "> **User** - test_author_mention\n"
            + "> **Channel** - test_channel\n"
            + "> **Error** - test_error_message\n"
            + f"> **Error type** - {type(self.error)}\n"
            + "> **Message** - test_message\n"
            + "> **Args** - test_args\n"
            + "> **Kwargs** - test_kwargs\n"
        )
        await self.Events.on_command_error(self.ctx, self.error)
        user.send.assert_called_with(test_error_message)

    async def test_command_error_forbidden_resolves(self) -> None:
        error = discord.errors.Forbidden(
            mock.MagicMock(status=403, reason="Forbidden"), "x"
        )
        await self.Events.on_command_error(self.ctx, error)
        self.ctx.reply.assert_awaited()

    async def test_app_command_error_checkfailure_resolves(self) -> None:
        await self.Events.on_application_command_error(
            self.ctx, discord.errors.CheckFailure()
        )
        self.ctx.respond.assert_awaited()

    async def test_app_command_invoke_error_notifies_owner(self) -> None:
        owner = mock.AsyncMock()
        self.ctx.bot.get_user = mock.MagicMock(return_value=None)
        self.ctx.bot.fetch_user = mock.AsyncMock(return_value=owner)
        self.ctx.command.name = "boom_cmd"

        try:
            raise ValueError("kaboom")
        except ValueError as exc:
            err = discord.ApplicationCommandInvokeError(exc)

        await self.Events.on_application_command_error(self.ctx, err)

        owner.send.assert_awaited()
        sent = owner.send.call_args.args[0]
        self.assertIn("kaboom", sent)
        self.ctx.respond.assert_awaited()

    async def test_command_error_branches_reply(self) -> None:
        for error in (
            UsagiNotSetUpError(),
            UsagiModuleDisabledError(),
            UsagiCallFromNotModerError(),
            UsagiCallFromWrongChannelError(channel_id=5),
            BadColourArgument("nope"),
            discord.errors.CheckFailure(),
        ):
            self.ctx.reply.reset_mock()
            await self.Events.on_command_error(self.ctx, error)
            self.ctx.reply.assert_awaited()

    async def test_app_command_error_branches_respond(self) -> None:
        cooldown = commands.CommandOnCooldown(
            cooldown=commands.Cooldown(rate=1, per=60.0),
            retry_after=30.0,
            type=commands.BucketType.user,
        )
        for error in (
            UsagiNotSetUpError(),
            cooldown,
            UsagiModuleDisabledError(),
            UsagiCallFromNotModerError(),
            UsagiCallFromWrongChannelError(channel_id=5),
            BadColourArgument("nope"),
        ):
            self.ctx.respond.reset_mock()
            await self.Events.on_application_command_error(self.ctx, error)
            self.ctx.respond.assert_awaited()

    async def test_app_command_error_unknown_notifies_owner(self) -> None:
        owner = mock.AsyncMock()
        self.ctx.bot.get_user = mock.MagicMock(return_value=None)
        self.ctx.bot.fetch_user = mock.AsyncMock(return_value=owner)
        self.ctx.command.name = "cmd"

        await self.Events.on_application_command_error(self.ctx, ValueError("x"))

        owner.send.assert_awaited()


class TestSaveRoles(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        self.bot = mock.MagicMock()
        from usagiBot.cogs.Events.index import Events

        self.Events = Events(self.bot)
        self.bot.i18n = init_i18n()
        self.bot.language = {}

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiMemberRoles", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Events.index.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiSaveRoles", new_callable=mock.AsyncMock
    )
    async def test_on_member_remove_skips_when_disabled(
        self, mock_Save, mock_Config, mock_Member
    ) -> None:
        mock_Save.get.return_value = mock.MagicMock(saving_roles=False)
        member = mock.AsyncMock()
        member.guild.id = "g1"
        member.roles = [mock.MagicMock(id=1)]
        member.roles[0].is_assignable.return_value = True

        await self.Events.on_member_remove(member)

        mock_Member.create.assert_not_called()
        mock_Member.update.assert_not_called()

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiMemberRoles", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Events.index.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiSaveRoles", new_callable=mock.AsyncMock
    )
    async def test_on_member_join_skips_deleted_roles(
        self, mock_Save, mock_Config, mock_Member
    ) -> None:
        mock_Save.get.return_value = mock.MagicMock(saving_roles=True)
        mock_Config.get.return_value = mock.MagicMock(generic_id=1)
        mock_Member.get.return_value = mock.MagicMock(roles="1,2")

        live_role = mock.MagicMock(id=1)
        member = mock.AsyncMock()

        def get_role(role_id):
            return live_role if role_id == 1 else None

        member.guild.get_role = mock.MagicMock(side_effect=get_role)
        # cache miss -> fall through to (awaited) fetch_channel
        member.guild.get_channel = mock.MagicMock(return_value=None)

        await self.Events.on_member_join(member)

        member.add_roles.assert_awaited_once()
        self.assertNotIn(None, member.add_roles.await_args.args)
        self.assertIn(live_role, member.add_roles.await_args.args)

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiMemberRoles", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Events.index.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiSaveRoles", new_callable=mock.AsyncMock
    )
    async def test_on_member_join_prefers_channel_cache(
        self, mock_Save, mock_Config, mock_Member
    ) -> None:
        mock_Save.get.return_value = mock.MagicMock(saving_roles=True)
        mock_Config.get.return_value = mock.MagicMock(generic_id=7)
        mock_Member.get.return_value = mock.MagicMock(roles="1")

        member = mock.AsyncMock()
        member.guild.get_role = mock.MagicMock(return_value=mock.MagicMock(id=1))
        cached = mock.AsyncMock()
        member.guild.get_channel = mock.MagicMock(return_value=cached)

        await self.Events.on_member_join(member)

        member.guild.get_channel.assert_called_once_with(7)
        member.guild.fetch_channel.assert_not_called()
        cached.send.assert_awaited()

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiMemberRoles", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Events.index.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiSaveRoles", new_callable=mock.AsyncMock
    )
    async def test_on_member_remove_creates_when_absent(
        self, mock_Save, mock_Config, mock_Member
    ) -> None:
        mock_Save.get.return_value = mock.MagicMock(saving_roles=True)
        mock_Config.get.return_value = mock.MagicMock(generic_id=7)
        mock_Member.get.return_value = None  # no saved row yet

        member = mock.AsyncMock()
        member.guild.id = "g1"
        member.id = "u1"
        role = mock.MagicMock(id=5)
        role.is_assignable.return_value = True
        member.roles = [role]
        member.guild.get_channel = mock.MagicMock(return_value=mock.AsyncMock())

        await self.Events.on_member_remove(member)

        mock_Member.create.assert_awaited_once()
        self.assertEqual(mock_Member.create.await_args.kwargs["roles"], "5")

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiMemberRoles", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Events.index.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiSaveRoles", new_callable=mock.AsyncMock
    )
    async def test_on_member_remove_updates_when_present(
        self, mock_Save, mock_Config, mock_Member
    ) -> None:
        mock_Save.get.return_value = mock.MagicMock(saving_roles=True)
        mock_Config.get.return_value = mock.MagicMock(generic_id=7)
        mock_Member.get.return_value = mock.MagicMock(id=42)

        member = mock.AsyncMock()
        member.guild.id = "g1"
        member.id = "u1"
        role = mock.MagicMock(id=5)
        role.is_assignable.return_value = True
        member.roles = [role]
        member.guild.get_channel = mock.MagicMock(return_value=mock.AsyncMock())

        await self.Events.on_member_remove(member)

        mock_Member.update.assert_awaited_once_with(id=42, roles="5")


class TestReactionRoles(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        self.bot = mock.MagicMock()
        self.bot.user.id = 999
        self.bot.ai_questions = {}
        self.bot.wait_until_ready = mock.AsyncMock()
        from usagiBot.cogs.Events.index import Events

        self.Events = Events(self.bot)

    def _payload(self):
        payload = mock.MagicMock()
        payload.message_id = 111
        payload.user_id = 1
        payload.guild_id = "g1"
        payload.channel_id = "c1"
        payload.emoji = mock.MagicMock(id=7)
        return payload

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiAutoRolesData", new_callable=mock.AsyncMock
    )
    async def test_reaction_add_assigns_role(self, mock_Data) -> None:
        self.bot.auto_roles = {"g1": {"111": {"channel_id": "c1"}}}
        mock_Data.get.return_value = mock.MagicMock(role_id=55)

        guild = mock.MagicMock()
        role = mock.MagicMock()
        guild.get_role = mock.MagicMock(return_value=role)
        member = mock.AsyncMock()
        guild.get_member = mock.MagicMock(return_value=member)
        self.bot.get_guild = mock.MagicMock(return_value=guild)

        await self.Events.on_raw_reaction_add(self._payload())

        member.add_roles.assert_awaited_once_with(role)

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiAutoRolesData", new_callable=mock.AsyncMock
    )
    async def test_reaction_add_skips_unknown_message(self, mock_Data) -> None:
        self.bot.auto_roles = {}
        await self.Events.on_raw_reaction_add(self._payload())
        mock_Data.get.assert_not_called()

    @mock.patch(
        "usagiBot.cogs.Events.index.UsagiAutoRolesData", new_callable=mock.AsyncMock
    )
    async def test_reaction_remove_removes_role(self, mock_Data) -> None:
        self.bot.auto_roles = {"g1": {"111": {"channel_id": "c1"}}}
        mock_Data.get.return_value = mock.MagicMock(role_id=55)

        guild = mock.MagicMock()
        role = mock.MagicMock()
        guild.get_role = mock.MagicMock(return_value=role)
        member = mock.AsyncMock()
        guild.get_member = mock.MagicMock(return_value=member)
        self.bot.get_guild = mock.MagicMock(return_value=guild)

        await self.Events.on_raw_reaction_remove(self._payload())

        member.remove_roles.assert_awaited_once_with(role)

    async def test_reaction_add_ignores_bot_self(self) -> None:
        payload = self._payload()
        payload.user_id = 999  # the bot itself
        self.bot.auto_roles = {}
        await self.Events.on_raw_reaction_add(payload)  # must not raise


class TestOnMessageCounters(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        self.bot = mock.MagicMock()
        self.bot.messages_dump = {}
        self.bot.wait_until_ready = mock.AsyncMock()
        from usagiBot.cogs.Events.index import Events

        self.Events = Events(self.bot)
        self.bot.messages_dump = {}

    def _message(self):
        message = mock.MagicMock()
        message.author.bot = False
        message.author.id = "u1"
        message.channel = mock.MagicMock(spec=discord.TextChannel)
        message.channel.id = "c1"
        message.guild.id = "g1"
        message.attachments = []
        message.stickers = []
        message.content = ""
        return message

    async def test_counts_message_and_emoji(self) -> None:
        message = self._message()
        message.content = "hello <:pepe:1234567890>"
        await self.Events.on_message(message)
        counters = self.bot.messages_dump["g1"]["c1"]["u1"]
        self.assertEqual(counters["messages"], 1)
        self.assertEqual(counters["emojis"], 1)

    async def test_counts_image_gif_sticker(self) -> None:
        message = self._message()
        png = mock.MagicMock(content_type="image/png")
        gif = mock.MagicMock(content_type="image/gif")
        message.attachments = [png, gif]
        message.content = "look .gif"
        message.stickers = [mock.MagicMock(), mock.MagicMock()]
        await self.Events.on_message(message)
        counters = self.bot.messages_dump["g1"]["c1"]["u1"]
        self.assertEqual(counters["images"], 1)
        self.assertEqual(counters["gifs"], 2)  # attachment gif + ".gif" in content
        self.assertEqual(counters["stickers"], 2)

    async def test_ignores_bots(self) -> None:
        message = self._message()
        message.author.bot = True
        await self.Events.on_message(message)
        self.assertEqual(self.bot.messages_dump, {})

    async def test_ignores_dm(self) -> None:
        message = self._message()
        message.channel = mock.MagicMock(spec=discord.DMChannel)
        await self.Events.on_message(message)
        self.assertEqual(self.bot.messages_dump, {})


class TestEventsSetup(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def test_setup_adds_cog(self, mock_engine) -> None:
        from usagiBot.cogs.Events.index import setup

        bot = mock.MagicMock()
        setup(bot)
        bot.add_cog.assert_called_once()


class TestCustomEmojiPattern(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Events import index as events_index

        self.pattern = events_index.CUSTOM_EMOJI_RE

    def test_matches_custom_emoji(self) -> None:
        self.assertTrue(self.pattern.search("hi <:pepe:1234567890>"))

    def test_matches_animated_emoji(self) -> None:
        self.assertTrue(self.pattern.search("<a:dinkDonk:865127621112102953>"))

    def test_ignores_plain_colons(self) -> None:
        self.assertFalse(self.pattern.search("meet at 12:30, ok :> friend"))


class TestOnReady(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        self.bot = mock.AsyncMock()
        self.bot.logger = mock.MagicMock()
        from usagiBot.cogs.Events.index import Events

        self.Events = Events(self.bot)

    @mock.patch(
        "usagiBot.cogs.Events.index.init_auto_roles", new_callable=mock.AsyncMock
    )
    @mock.patch(
        "usagiBot.cogs.Events.index.init_moder_roles", new_callable=mock.AsyncMock
    )
    @mock.patch(
        "usagiBot.cogs.Events.index.init_cogs_settings", new_callable=mock.AsyncMock
    )
    @mock.patch(
        "usagiBot.cogs.Events.index.load_all_command_tags", new_callable=mock.AsyncMock
    )
    async def test_on_ready_syncs_commands_once(self, *_mocks) -> None:
        await self.Events.on_ready()
        await self.Events.on_ready()

        self.assertEqual(self.bot.sync_commands.await_count, 1)


class TestDumpData(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiBackup", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_UsagiBackup) -> None:
        self.bot = mock.MagicMock()
        from usagiBot.cogs.Events.index import Events

        self.Events = Events(self.bot)

    @mock.patch("usagiBot.cogs.Events.index.UsagiBackup", new_callable=mock.AsyncMock)
    async def test_dump_data_upserts_counters(self, mock_backup) -> None:
        counters = {"messages": 3, "images": 1, "gifs": 0, "emojis": 2, "stickers": 0}
        self.bot.messages_dump = {"g1": {"c1": {"u1": dict(counters)}}}

        await self.Events.dump_data()

        mock_backup.upsert_add.assert_awaited_once_with(
            [
                {
                    "guild_id": "g1",
                    "channel_id": "c1",
                    "user_id": "u1",
                    "messages": 3,
                    "images": 1,
                    "gifs": 0,
                    "emojis": 2,
                    "stickers": 0,
                }
            ],
            conflict_columns=["guild_id", "channel_id", "user_id"],
            counter_columns=["messages", "images", "gifs", "emojis", "stickers"],
        )
        mock_backup.get_all.assert_not_called()
        mock_backup.get_last_obj.assert_not_called()
        mock_backup.insert_mappings.assert_not_called()
        mock_backup.delete_all.assert_not_called()
        self.assertEqual(self.bot.messages_dump, {})

    @mock.patch("usagiBot.cogs.Events.index.UsagiBackup", new_callable=mock.AsyncMock)
    async def test_dump_data_skips_db_when_empty(self, mock_backup) -> None:
        self.bot.messages_dump = {}

        await self.Events.dump_data()

        mock_backup.upsert_add.assert_not_called()

    @mock.patch("usagiBot.cogs.Events.index.UsagiBackup", new_callable=mock.AsyncMock)
    async def test_dump_data_restores_counts_on_upsert_failure(
        self, mock_backup
    ) -> None:
        zero = {"messages": 0, "images": 0, "gifs": 0, "emojis": 0, "stickers": 0}
        self.bot.messages_dump = {"g1": {"c1": {"u1": {**zero, "messages": 3}}}}

        async def boom(*args, **kwargs):
            # a message arrives mid-flush, after the dict was swapped out
            self.bot.messages_dump.setdefault("g1", {}).setdefault(
                "c1", {}
            ).setdefault("u1", dict(zero))["messages"] += 1
            raise Exception("db down")

        mock_backup.upsert_add.side_effect = boom

        await self.Events.dump_data()  # must not raise

        mock_backup.upsert_add.assert_awaited_once()
        self.bot.logger.exception.assert_called()
        # 3 restored + 1 that arrived during the failed flush
        self.assertEqual(self.bot.messages_dump["g1"]["c1"]["u1"]["messages"], 4)
