import importlib

from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestTechUtils(IsolatedAsyncioTestCase):

    @mock.patch("usagiBot.db.models.UsagiUnicRoles", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    async def test_get_user_roles(self, mock_engine, mock_UsagiUnicRoles) -> None:
        ctx = mock.AsyncMock()
        ctx.interaction.guild.id = "test_guild_id"
        ctx.interaction.user.id = "test_user_id"
        role_1 = mock.MagicMock()
        role_1.id = 111
        role_1.name = "role_name_1"
        role_2 = mock.MagicMock()
        role_2.id = 222
        role_2.name = "role_name_2"
        role_3 = mock.MagicMock()
        role_3.id = 333
        role_3.name = "role_name_3"
        role_4 = mock.MagicMock()
        role_4.id = 444
        role_4.name = "role_name_4"
        ctx.interaction.guild.fetch_roles.return_value = [role_1, role_2, role_3, role_4]

        role_ids = [
            mock.MagicMock(role_id=111),
            mock.MagicMock(role_id=444),
        ]

        import usagiBot.cogs.Tech.tech_utils as tech_utils
        importlib.reload(tech_utils)

        mock_UsagiUnicRoles.get_all_role_ids_by_user.return_value = role_ids
        guessed_result = await tech_utils.get_user_roles(ctx)

        mock_UsagiUnicRoles.get_all_role_ids_by_user.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
        )

        self.assertEqual(2, len(guessed_result))
        self.assertEqual("role_name_1", guessed_result[0].name)
        self.assertEqual("111", guessed_result[0].value)
        self.assertEqual("role_name_4", guessed_result[1].name)
        self.assertEqual("444", guessed_result[1].value)

    @mock.patch("usagiBot.db.models.UsagiUnicRoles", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    async def test_get_user_roles_no_roles(self, mock_engine, mock_UsagiUnicRoles) -> None:
        mock_UsagiUnicRoles.get_all_role_ids_by_user.return_value = None
        import usagiBot.cogs.Tech.tech_utils as tech_utils
        importlib.reload(tech_utils)
        ctx = mock.AsyncMock()
        result = await tech_utils.get_user_roles(ctx)
        self.assertEqual(result, [])

    @mock.patch("usagiBot.db.models.UsagiUnicRoles", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    async def test_get_user_role(self, mock_engine, mock_UsagiUnicRoles) -> None:

        import usagiBot.cogs.Tech.tech_utils as tech_utils
        ctx = mock.AsyncMock()
        ctx.guild.get_role = mock.MagicMock()
        ctx.guild.get_role.return_value = "test_role"

        with mock.patch("usagiBot.cogs.Tech.tech_utils.get_user_roles", return_value=[
            mock.MagicMock(value=111),
            mock.MagicMock(value=444),
        ]) as mock_get_user_roles:
            result = await tech_utils.get_user_role(ctx, 444)
            ctx.guild.get_role.assert_called_with(444)
            self.assertEqual(result, "test_role")

    @mock.patch("usagiBot.db.models.UsagiUnicRoles", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    async def test_get_user_role_not_user_role(self, mock_engine, mock_UsagiUnicRoles) -> None:
        import usagiBot.cogs.Tech.tech_utils as tech_utils
        ctx = mock.AsyncMock()
        ctx.guild.get_role = mock.MagicMock()
        ctx.guild.get_role.return_value = "test_role"

        with mock.patch("usagiBot.cogs.Tech.tech_utils.get_user_roles", return_value=[
            mock.MagicMock(value=111),
            mock.MagicMock(value=444),
        ]) as mock_get_user_roles:
            result = await tech_utils.get_user_role(ctx, 222)
            ctx.respond.assert_called_with("It's not your role or you didn't create it", ephemeral=True)
            self.assertIsNone(result)
