import datetime

from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestTechMethods(IsolatedAsyncioTestCase):

    @classmethod
    @mock.patch("usagiBot.cogs.Tech.tech_utils.get_user_role", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.models.UsagiUnicRoles", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUpClass(cls, mock_engine, mock_UsagiUnicRoles, mock_get_user_role) -> None:
        cls.mock_UsagiUnicRoles = mock_UsagiUnicRoles
        from usagiBot.cogs.Tech.index import Tech
        cls.Tech = Tech
        cls.role = mock.AsyncMock(id="test_role_id", mention="test_role_mention")
        mock_get_user_role.return_value = cls.role

        cls.bot = mock.AsyncMock()
        cls.ctx = mock.AsyncMock()
        cls.ctx.author.name = "test_author"
        cls.ctx.author.id = "test_author_id"
        cls.ctx.guild.id = "test_guild_id"
        cls.ctx.guild.create_role.return_value = cls.role

        cls.message = mock.AsyncMock()

    async def test_pin_message(self) -> None:

        await self.Tech.pin_message(self.Tech, self.ctx, self.message)

        self.message.pin.assert_called_with(reason=f"Pinned by test_author")
        self.ctx.respond.assert_called_with(f"Message was pinned", ephemeral=True)

    async def test_go_sleep(self) -> None:
        await self.Tech.go_sleep(self.ctx, 20)
        self.ctx.author.timeout_for.assert_called_with(
            duration=datetime.timedelta(seconds=72000),
            reason="Timeout for sleep"
        )
        self.ctx.respond.assert_called_with("Good night, see you in 20 hours.", ephemeral=True)

    async def test_go_sleep_wrong_hours(self) -> None:
        await self.Tech.go_sleep(self.ctx, 80)
        self.ctx.respond.assert_called_with("You entered the wrong amount of time.", ephemeral=True)

    async def test_create_new_unic_role(self) -> None:
        await self.Tech.create_new_unic_role(self.ctx, "test_role_name", "111")
        self.ctx.guild.create_role.assert_called_with(
            name="test_role_name",
            colour="111",
            hoist=True,
            mentionable=True,
            reason=f"New role by test_author, id = test_author_id"
        )
        self.ctx.author.add_roles.assert_called_with(self.role)
        self.mock_UsagiUnicRoles.create.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_author_id",
            role_id="test_role_id",
        )
        self.ctx.respond.assert_called_with(
            "Created a new role for you. :point_right::skin-tone-1: test_role_mention",
            ephemeral=True
        )

    async def test_delete_unic_role(self) -> None:
        await self.Tech.delete_unic_role(self.ctx, "test_role_name")
        self.mock_UsagiUnicRoles.delete.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_author_id",
            role_id="test_role_id",
        )
        self.ctx.author.remove_roles.assert_called_with(self.role)
        self.ctx.respond.assert_called_with("Successfully removed your role", ephemeral=True)

    async def test_rename_unic_role(self) -> None:
        await self.Tech.rename_unic_role(self.ctx, "test_role_name", "new_name_role")
        self.role.edit.assert_called_with(name="new_name_role")
        self.ctx.respond.assert_called_with(
            f"Successfully renamed your role :point_right::skin-tone-1: test_role_mention",
            ephemeral=True
        )

    async def test_recolor_unic_role(self) -> None:
        await self.Tech.recolor_unic_role(self.ctx, "test_role_name", "new_color_role")
        self.role.edit.assert_called_with(color="new_color_role")
        self.ctx.respond.assert_called_with(
            f"Successfully recolored your role :point_right::skin-tone-1: test_role_mention",
            ephemeral=True
        )
