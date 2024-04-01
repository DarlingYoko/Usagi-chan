from discord import SlashCommandGroup
from discord.ext import commands
from datetime import timedelta

from discord.ext.commands import ColorConverter

from usagiBot.src.UsagiChecks import check_cog_whitelist, check_correct_channel_command, check_member_is_moder
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.cogs.Tech.tech_utils import *

from pycord18n.extension import _


class Tech(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.message_command(name="Pin message", name_localizations={"ru": "Закрепить сообщение"},)
    async def pin_message(self, ctx, message: discord.Message) -> None:
        await message.pin(reason=f"Pinned by {ctx.author.name}")
        await ctx.respond(_("Message was pinned"), ephemeral=True)

    @commands.slash_command()
    @commands.check(check_member_is_moder)
    async def purge(self, ctx, limit: int):
        await ctx.channel.purge(limit = limit + 1)
        await ctx.respond('Успешно удалила', delete_after = 10)

    @commands.slash_command(
        name="sleep",
        name_localizations={"ru": "спать"},
        description="Go to sleep for N hours",
        description_localizations={"ru": "Заснуть на время."},
    )
    @discord.commands.option(
        name="hours",
        name_localizations={"ru": "часы"},
        description="Insert sleep hours!",
        description_localizations={"ru": "На сколько заснуть."},
        choices=map(lambda x: str(x), range(2, 25, 2)),
    )
    async def go_sleep(
            self,
            ctx,
            hours: int,
    ) -> None:
        duration = timedelta(hours=hours)
        await ctx.author.timeout_for(duration=duration, reason="Timeout for sleep")
        await ctx.respond(_("Good night, see you in").format(hours=hours), ephemeral=True)

    unic_role = SlashCommandGroup(
        name="unic_role",
        name_localizations={"ru": "уникальная_роль"},
        description="Customize your own role on the server!",
        description_localizations={"ru": "Создай свою собственную роль на сервере!"},
        checks=[
            check_correct_channel_command().predicate
        ],
        command_tag="customize_role",
    )

    customize_role_modify = unic_role.create_subgroup(
        name="modify",
        name_localizations={"ru": "изменить"},
        description="Modify an already created role!",
        description_localizations={"ru": "Измени свою роль если захочется!"},
    )

    @unic_role.command(
        name="create",
        name_localizations={"ru": "создать"},
        description="Create your own role for yourself.",
        description_localizations={"ru": "Создать себе роль."},
    )
    @discord.commands.option(
        name="name",
        name_localizations={"ru": "имя"},
        description="Name for the new role",
        description_localizations={"ru": "Название роли."},
    )
    @discord.commands.option(
        name="color",
        name_localizations={"ru": "цвет"},
        description="Color for the new role in hexadecimal",
        description_localizations={"ru": "Цвет твоей роли в шестнадцатеричной системе."},
    )
    async def create_new_unic_role(
            self,
            ctx,
            name: str,
            color: ColorConverter
    ) -> None:
        role = await ctx.guild.create_role(
            name=name,
            colour=color,
            hoist=True,
            mentionable=True,
            reason=f"New role by {ctx.author.name}, id = {ctx.author.id}"
        )
        await ctx.author.add_roles(role)
        await UsagiUnicRoles.create(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            role_id=role.id,
        )
        await ctx.respond(_("Created a new role for you").format(mention=role.mention), ephemeral=True)

    @unic_role.command(
        name="delete",
        name_localizations={"ru": "удалить"},
        description="Delete your role.",
        description_localizations={"ru": "Удалить свою роль."},
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a role to delete.",
        description_localizations={"ru": "Выбери роль, которую надо удалить."},
        autocomplete=get_user_roles,
    )
    async def delete_unic_role(
            self,
            ctx,
            role,
    ) -> None:
        role = await get_user_role(ctx, role)
        if role:
            await UsagiUnicRoles.delete(
                guild_id=ctx.guild.id,
                user_id=ctx.author.id,
                role_id=role.id,
            )
            await ctx.author.remove_roles(role)
            await ctx.respond(_("Successfully removed your role"), ephemeral=True)

    @customize_role_modify.command(
        name="name",
        name_localizations={"ru": "имя"},
        description="Change name of your role.",
        description_localizations={"ru": "Измени имя своей роли."},
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a role to rename.",
        description_localizations={"ru": "Выбери роль для изменения."},
        autocomplete=get_user_roles,
    )
    async def rename_unic_role(
            self,
            ctx,
            role,
            new_name: str
    ) -> None:
        role = await get_user_role(ctx, role)
        if role:
            await role.edit(name=new_name)
            await ctx.respond(
                _("Successfully renamed your role").format(mention=role.mention),
                ephemeral=True
            )

    @customize_role_modify.command(
        name="color",
        name_localizations={"ru": "цвет"},
        description="Change color of your role.",
        description_localizations={"ru": "Измени цвет своей роли."},
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a role to recolor.",
        description_localizations={"ru": "Выбери роль для изменения."},
        autocomplete=get_user_roles,
    )
    async def recolor_unic_role(
            self,
            ctx,
            role,
            new_color: ColorConverter
    ) -> None:
        role = await get_user_role(ctx, role)
        if role:
            await role.edit(color=new_color)
            await ctx.respond(
                _("Successfully recolored your role").format(mention=role.mention),
                ephemeral=True
            )


def setup(bot):
    bot.add_cog(Tech(bot))
