"""Permission checks: role hierarchy, admin-only setup, guild-only commands."""
import sys
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase, mock

import discord
import pytest
from discord.ext import commands
from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *

OWNER_ID = int(os.environ["BOT_OWNER"])


@pytest.fixture(autouse=True)
def clear_imports():
    from usagiBot.db.base import Base

    Base.metadata.clear()
    initial_modules = dict(sys.modules)
    yield
    for module in list(sys.modules.keys()):
        if module not in initial_modules:
            del sys.modules[module]


def make_role(
    position: int = 5,
    managed: bool = False,
    default: bool = False,
    assignable: bool = True,
    **permissions: bool,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=500 + position,
        position=position,
        managed=managed,
        permissions=discord.Permissions(**permissions),
        is_default=lambda: default,
        is_assignable=lambda: assignable,
    )


def make_member(
    top_position: int = 10, member_id: int = 1, guild_owner_id: int = 999, **perms: bool
) -> SimpleNamespace:
    return SimpleNamespace(
        id=member_id,
        guild=SimpleNamespace(owner_id=guild_owner_id),
        top_role=SimpleNamespace(position=top_position),
        guild_permissions=discord.Permissions(**perms),
    )


def make_ctx(member=None, guild: bool = True) -> mock.MagicMock:
    ctx = mock.MagicMock()
    ctx.author = member or make_member()
    ctx.guild = mock.MagicMock(id=42, owner_id=999) if guild else None
    ctx.bot.moder_roles = {}
    ctx.author.roles = []
    return ctx


class TestRoleGrantError(TestCase):
    def setUp(self) -> None:
        from usagiBot.src.UsagiChecks import role_grant_error

        self.check = role_grant_error

    def test_plain_role_below_author_is_fine(self) -> None:
        self.assertIsNone(self.check(make_member(top_position=10), make_role(5)))

    def test_role_at_or_above_author_top_role(self) -> None:
        member = make_member(top_position=5)

        for position in (5, 6):
            with self.subTest(position=position):
                self.assertEqual(
                    self.check(member, make_role(position)),
                    "You can only give out roles below your highest role",
                )

    def test_elevated_role_needs_administrator(self) -> None:
        for permission in ("administrator", "manage_roles", "ban_members", "mention_everyone"):
            with self.subTest(permission=permission):
                self.assertEqual(
                    self.check(make_member(), make_role(**{permission: True})),
                    "Only administrators can give out roles with moderation permissions",
                )

    def test_administrator_may_bind_elevated_role(self) -> None:
        member = make_member(administrator=True)

        self.assertIsNone(self.check(member, make_role(manage_messages=True)))

    def test_default_and_managed_roles_are_never_grantable(self) -> None:
        owner = make_member(member_id=999)
        for role in (make_role(default=True), make_role(managed=True)):
            with self.subTest(role=role):
                self.assertEqual(self.check(owner, role), "This role can't be given out")

    def test_role_above_the_bot(self) -> None:
        self.assertEqual(
            self.check(make_member(member_id=999), make_role(assignable=False)),
            "This role is above my highest role",
        )

    def test_guild_owner_and_bot_owner_skip_hierarchy(self) -> None:
        role = make_role(50, administrator=True)

        self.assertIsNone(self.check(make_member(top_position=1, member_id=999), role))
        self.assertIsNone(self.check(make_member(top_position=1, member_id=OWNER_ID), role))


class TestGuildAndAdminChecks(TestCase):
    def setUp(self) -> None:
        from usagiBot.src import UsagiChecks
        from usagiBot.src.UsagiErrors import UsagiCallFromNotModerError

        self.checks = UsagiChecks
        self.NotModer = UsagiCallFromNotModerError

    def test_moder_check_in_dm(self) -> None:
        with self.assertRaises(commands.NoPrivateMessage):
            self.checks.check_member_is_moder(make_ctx(guild=False))

    def test_admin_check(self) -> None:
        self.assertTrue(
            self.checks.check_member_is_admin(make_ctx(make_member(administrator=True)))
        )
        self.assertTrue(self.checks.check_member_is_admin(make_ctx(make_member(member_id=999))))
        self.assertTrue(
            self.checks.check_member_is_admin(make_ctx(make_member(member_id=OWNER_ID)))
        )

    def test_moderator_is_not_admin(self) -> None:
        ctx = make_ctx(make_member(manage_guild=False))
        ctx.bot.moder_roles = {42: [7]}
        ctx.author.roles = [SimpleNamespace(id=7)]

        self.assertTrue(self.checks.check_member_is_moder(ctx))
        with self.assertRaises(self.NotModer):
            self.checks.check_member_is_admin(ctx)

    def test_admin_check_in_dm(self) -> None:
        with self.assertRaises(commands.NoPrivateMessage):
            self.checks.check_member_is_admin(make_ctx(guild=False))

    def test_pin_check(self) -> None:
        self.assertTrue(
            self.checks.check_member_can_pin(make_ctx(make_member(manage_messages=True)))
        )
        with self.assertRaises(self.NotModer):
            self.checks.check_member_can_pin(make_ctx())

    def test_pin_check_accepts_bot_moderators(self) -> None:
        ctx = make_ctx()
        ctx.bot.moder_roles = {42: [7]}
        ctx.author.roles = [SimpleNamespace(id=7)]

        self.assertTrue(self.checks.check_member_can_pin(ctx))

    def test_require_guild(self) -> None:
        self.assertTrue(self.checks.require_guild(make_ctx()))
        with self.assertRaises(commands.NoPrivateMessage):
            self.checks.require_guild(make_ctx(guild=False))


class TestSetUpCheckInDm(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    async def test_setup_check_rejects_dm_before_db(self, _engine) -> None:
        from usagiBot.src.UsagiChecks import check_is_already_set_up

        ctx = make_ctx(guild=False)
        ctx.command.parent = None
        ctx.command.__original_kwargs__ = {"command_tag": "x"}

        with mock.patch("usagiBot.src.UsagiChecks.UsagiConfig") as config:
            with self.assertRaises(commands.NoPrivateMessage):
                await check_is_already_set_up().predicate(ctx)
        config.get.assert_not_called()


def check_names(command) -> list:
    # compared by name: tests re-import modules, so function identity differs
    return [check.__name__ for check in command.checks]


class TestCommandWiring(IsolatedAsyncioTestCase):
    """The checks only run through py-cord, so assert they are attached."""

    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, _engine) -> None:
        pass

    def test_pin_requires_permission(self) -> None:
        from usagiBot.cogs.Tech.index import Tech

        self.assertIn("check_member_can_pin", check_names(Tech.pin_message))

    def test_birthday_timers_require_moderator(self) -> None:
        from usagiBot.cogs.Birthdays.index import Birthday

        for command in (Birthday.toggle_timer, Birthday.add_birthday_timer):
            with self.subTest(command=command.name):
                self.assertIn("check_member_is_moder", check_names(command))

    def test_moder_role_setup_requires_admin(self) -> None:
        from usagiBot.cogs.Moderation.index import Moderation

        for command in (Moderation.add_new_moder_role, Moderation.remove_moder_role):
            with self.subTest(command=command.name):
                self.assertIn("check_member_is_admin", check_names(command))

    def test_guild_cogs_reject_dm(self) -> None:
        from usagiBot.cogs.ArknightsEndfield.index import Endfield
        from usagiBot.cogs.Birthdays.index import Birthday
        from usagiBot.cogs.Hoyolab.index import Hoyolab
        from usagiBot.cogs.Tech.index import Tech
        from usagiBot.cogs.Twitch.index import Twitch

        ctx = make_ctx(guild=False)
        for cog in (Endfield, Birthday, Hoyolab, Tech, Twitch):
            with self.subTest(cog=cog.__name__):
                with self.assertRaises(commands.NoPrivateMessage):
                    cog.cog_check(mock.MagicMock(), ctx)

    def test_help_is_guild_only(self) -> None:
        from usagiBot.cogs.Main.index import Main

        self.assertEqual(Main.help_command.contexts, {discord.InteractionContextType.guild})


class TestModerRoleSetup(IsolatedAsyncioTestCase):
    @mock.patch(
        "usagiBot.cogs.Moderation.schemas.UsagiModerRoles", new_callable=mock.AsyncMock
    )
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, _engine, mock_ModerRoles) -> None:
        from usagiBot.cogs.Moderation.index import Moderation

        self.Moderation = Moderation
        self.mock_ModerRoles = mock_ModerRoles
        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = 42
        self.ctx.bot.moder_roles = {}
        init_i18n()

    async def test_everyone_cannot_become_moderator(self) -> None:
        everyone = mock.MagicMock(id=42)
        everyone.is_default.return_value = True

        await self.Moderation.add_new_moder_role.callback(
            self.Moderation, self.ctx, everyone
        )

        self.mock_ModerRoles.create.assert_not_called()
        self.assertEqual(self.ctx.bot.moder_roles, {})
        self.assertEqual(
            self.ctx.respond.call_args.kwargs["content"],
            "@everyone can't be a moderation role.",
        )


class TestAutoRoleGrantCheck(IsolatedAsyncioTestCase):
    @mock.patch(
        "usagiBot.cogs.Main.schemas.UsagiAutoRolesData", new_callable=mock.AsyncMock
    )
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, _engine, mock_Data) -> None:
        from usagiBot.cogs.Main import index as main_index

        self.main_index = main_index
        self.Main = main_index.Main
        self.mock_Data = mock_Data
        self.Main.bot = mock.AsyncMock()
        init_i18n()
        self.ctx = mock.AsyncMock()
        self.ctx.guild_id = 42
        self.ctx.bot.auto_roles = {42: {"123": {"channel_id": 1, "name": "n"}}}
        msg = mock.AsyncMock()
        msg.embeds = [mock.MagicMock()]
        msg.reactions = []
        self.msg = msg
        channel = mock.AsyncMock()
        channel.fetch_message.return_value = msg
        self.ctx.guild.fetch_channel.return_value = channel

    async def test_add_rejects_ungrantable_role(self) -> None:
        with mock.patch.object(
            self.main_index, "role_grant_error", return_value="This role can't be given out"
        ) as check:
            await self.Main.add_reaction_role.callback(
                self.Main, self.ctx, "123", mock.MagicMock(), mock.MagicMock(), "d"
            )

        check.assert_called_once()
        self.mock_Data.create.assert_not_called()
        self.msg.edit.assert_not_called()
        self.assertEqual(
            self.ctx.respond.call_args.kwargs["embed"].title,
            "This role can't be given out.",
        )

    async def test_edit_rejects_ungrantable_new_role(self) -> None:
        self.ctx.send_followup = mock.AsyncMock()
        with mock.patch.object(
            self.main_index,
            "role_grant_error",
            return_value="You can only give out roles below your highest role",
        ):
            await self.Main.edit_role_reaction_role.callback(
                self.Main, self.ctx, "123", "555", mock.MagicMock(id=777)
            )

        self.mock_Data.update.assert_not_called()
        self.msg.edit.assert_not_called()
        self.assertEqual(
            self.ctx.send_followup.call_args.kwargs["embed"].title,
            "You can only give out roles below your highest role.",
        )
