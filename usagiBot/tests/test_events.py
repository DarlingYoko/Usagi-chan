import discord
from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from discord.ext import commands
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

        await self.Events.on_member_join(member)

        member.add_roles.assert_awaited_once()
        self.assertNotIn(None, member.add_roles.await_args.args)
        self.assertIn(live_role, member.add_roles.await_args.args)


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
