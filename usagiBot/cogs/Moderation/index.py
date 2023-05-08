import discord
from discord import SlashCommandGroup
from discord.ext import commands

from usagiBot.db.models import UsagiConfig, UsagiCogs, UsagiModerRoles
from usagiBot.src.UsagiUtils import check_arg_in_command_tags
from usagiBot.src.UsagiChecks import check_member_is_moder

from typing import Union, List
from pycord18n.extension import _


def get_command_tags(ctx: discord.AutocompleteContext) -> List[discord.commands.options.OptionChoice]:
    """
    Returns a list of command tags.
    """
    return ctx.bot.command_tags


def get_bot_cogs(ctx: discord.AutocompleteContext) -> List:
    """
    Returns a list of command tags.
    """
    no_access_cogs = ["Events", "Moderation", "Main"]
    cogs = []
    for name in ctx.bot.cogs:
        if name not in no_access_cogs:
            cogs.append(name)
    return cogs


class Moderation(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        return check_member_is_moder(ctx)

    setup = SlashCommandGroup(
        name="setup",
        name_localizations={"ru": "настройка"},
        description="Customize Usagi-chan perfectly for your server!",
        description_localizations={"ru": "Настройте Усаги идеально для вашего сервера!"},
    )

    command_setup = setup.create_subgroup(
        name="command",
        name_localizations={"ru": "команда"},
        description="Set up all the commands that are needed on the guild!",
        description_localizations={"ru": "Настройте команды, которые необходимы на вашем сервере!"},
    )

    role_setup = setup.create_subgroup(
        name="role",
        name_localizations={"ru": "роль"},
        description="Set up moder roles for your guild!",
        description_localizations={"ru": "Настройте роли модераторов на вашем сервере!"},
    )

    module_setup = setup.create_subgroup(
        name="module",
        name_localizations={"ru": "модуль"},
        description="Set up modules that are needed on the guild!",
        description_localizations={"ru": "Настройте модули, которые будут на вашем сервере!"},
    )

    @command_setup.command(
        name="add",
        name_localizations={"ru": "добавить"},
        description="Add settings for command.",
        description_localizations={"ru": "Настройте канал в которому будет привязана команда."},
    )
    @discord.commands.option(
        name="command",
        name_localizations={"ru": "комманда"},
        description="Pick a command!",
        description_localizations={"ru": "Выберите команду для настройки."},
        autocomplete=get_command_tags,
    )
    async def add_config_for_command(
        self,
        ctx,
        command: str,
        channel: Union[discord.TextChannel, discord.VoiceChannel],
    ) -> None:
        if not check_arg_in_command_tags(command, ctx.bot.command_tags):
            await ctx.respond(
                _("This argument does not exist for commands"), ephemeral=True
            )
            return
        command_config_exist = await UsagiConfig.get(guild_id=ctx.guild.id, command_tag=command)
        text_result = _("Successfully configured channel for command")
        if command_config_exist:
            await UsagiConfig.update(
                id=command_config_exist.id,
                guild_id=ctx.guild.id,
                command_tag=command,
                generic_id=channel.id
            )
            text_result = _("Successfully reconfigured channel for command")
        else:
            await UsagiConfig.create(
                guild_id=ctx.guild.id,
                command_tag=command,
                generic_id=channel.id
            )

        await ctx.respond(content=text_result, ephemeral=True)

    @command_setup.command(
        name="remove",
        name_localizations={"ru": "удалить"},
        description="Remove settings for command.",
        description_localizations={"ru": "Удалить настройку команды"},
    )
    @discord.commands.option(
        name="command",
        name_localizations={"ru": "комманда"},
        description="Pick a command!",
        description_localizations={"ru": "Выберите команду для удаления."},
        autocomplete=get_command_tags,
    )
    async def delete_config_for_command(
        self,
        ctx,
        command: str,
    ) -> None:

        if not check_arg_in_command_tags(command, ctx.bot.command_tags):
            await ctx.respond(
                content=_("This argument does not exist for commands"),
                ephemeral=True
            )
            return

        await UsagiConfig.delete(guild_id=ctx.guild.id, command_tag=command)

        await ctx.respond(content=_("Successfully deleted configure for command"), ephemeral=True)

    @module_setup.command(
        name="enable",
        name_localizations={"ru": "комманда"},
        description="Enable module in Usagi-chan.",
        description_localizations={"ru": "Включить модуль для сервера."},
    )
    @discord.commands.option(
        name="module",
        name_localizations={"ru": "модуль"},
        description="Pick a module!",
        description_localizations={"ru": "Выберите модуль для включения."},
        autocomplete=get_bot_cogs,
    )
    async def enable_module(
            self,
            ctx,
            module: str,
    ) -> None:
        guild_id = ctx.guild.id
        guild_cogs_settings = ctx.bot.guild_cogs_settings

        if module not in get_bot_cogs(ctx):
            await ctx.respond(
                content=_("This module isn't available"),
                ephemeral=True
            )
            return

        if (
            guild_id in guild_cogs_settings and
            module in guild_cogs_settings[guild_id]
        ):
            await ctx.respond(
                content=_("This module already enabled"),
                ephemeral=True
            )
            return

        await UsagiCogs.create(
            guild_id=guild_id,
            module_name=module,
            access=True,
        )
        if guild_id in guild_cogs_settings:
            guild_cogs_settings[guild_id][module] = True
        else:
            guild_cogs_settings[guild_id] = {module: True}

        await ctx.respond(
            content=_("The module has been enabled").format(module=module),
            ephemeral=True
        )
        return

    @module_setup.command(
        name="disable",
        name_localizations={"ru": "отключить"},
        description="Disable module in Usagi-chan.",
        description_localizations={"ru": "Отключить модуль для сервера."},
    )
    @discord.commands.option(
        name="module",
        name_localizations={"ru": "модуль"},
        description="Pick a module!",
        description_localizations={"ru": "Выберите модуль для отключения."},
        autocomplete=get_bot_cogs,
    )
    async def disable_module(
            self,
            ctx,
            module: str,
    ) -> None:
        guild_id = ctx.guild.id
        guild_cogs_settings = ctx.bot.guild_cogs_settings

        if module not in get_bot_cogs(ctx):
            await ctx.respond(
                content=_("This module isn't available"),
                ephemeral=True
            )
            return

        if (
            guild_id not in guild_cogs_settings or
            (guild_id in guild_cogs_settings and module not in guild_cogs_settings[guild_id])
        ):
            await ctx.respond(
                content=_("This module isn't enabled."),
                ephemeral=True
            )
            return

        await UsagiCogs.delete(
            guild_id=guild_id,
            module_name=module,
        )

        del guild_cogs_settings[guild_id][module]
        if len(guild_cogs_settings[guild_id]) == 0:
            del guild_cogs_settings[guild_id]

        await ctx.respond(
            content=_("The module has been disabled").format(module=module),
            ephemeral=True
        )
        return

    @role_setup.command(
        name="add",
        name_localizations={"ru": "добавить"},
        description="Add new moder role for guild.",
        description_localizations={"ru": "Добавить новую модер роль для сервера."},
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a Role!",
        description_localizations={"ru": "Выберите роль."},
    )
    async def add_new_moder_role(
            self,
            ctx,
            member_role: discord.Role,
    ) -> None:
        guild_id = ctx.guild.id
        moder_roles = ctx.bot.moder_roles
        if (
            guild_id in moder_roles and
            member_role.id in moder_roles[guild_id]
        ):
            await ctx.respond(content=_("This role already added"), ephemeral=True)
            return

        await UsagiModerRoles.create(
            guild_id=guild_id,
            moder_role_id=member_role.id,
        )
        if moder_roles.get(guild_id) is not None:
            moder_roles[guild_id].append(member_role.id)
        else:
            moder_roles[guild_id] = [member_role.id]

        await ctx.respond(
            content=_("The role has been added").format(member_role=member_role.mention),
            ephemeral=True
        )
        return

    @role_setup.command(
        name="remove",
        name_localizations={"ru": "удалить"},
        description="Remove moder role from guild.",
        description_localizations={"ru": "Удалить модер роль с сервера."},
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a Role!",
        description_localizations={"ru": "Выберите роль."},
    )
    async def remove_moder_role(
            self,
            ctx,
            member_role: Union[discord.Role],
    ) -> None:
        guild_id = ctx.guild.id
        moder_roles = ctx.bot.moder_roles

        if (
            moder_roles.get(guild_id) is None or
            (moder_roles.get(guild_id) is not None and member_role.id not in moder_roles[guild_id])
        ):
            await ctx.respond(content=_("This role isn't moderation"), ephemeral=True)
            return

        await UsagiModerRoles.delete(
            guild_id=guild_id,
            moder_role_id=member_role.id,
        )

        moder_roles[guild_id].remove(member_role.id)
        if len(moder_roles[guild_id]) == 0:
            del moder_roles[guild_id]

        await ctx.respond(
            content=_("The role has been removed").format(member_role=member_role.mention),
            ephemeral=True
        )
        return

    @role_setup.command(
        name="show",
        name_localizations={"ru": "показать"},
        description="Show all moder roles from that guild.",
        description_localizations={"ru": "Показать все модер роли на этом сервере."},
    )
    async def show_moder_roles(
            self,
            ctx,
    ) -> None:
        guild_id = ctx.guild.id
        moder_roles = ctx.bot.moder_roles
        if guild_id not in moder_roles:
            await ctx.respond(content=_("This guild doesn't have any Moderation roles"), ephemeral=True)
            return

        result_text = _("All moderation roles:\n")
        counter = 1
        for role_id in moder_roles[guild_id]:
            result_text += f"{counter}. <@&{role_id}>\n"
            counter += 1

        await ctx.respond(content=result_text, ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
