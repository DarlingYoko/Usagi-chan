import discord
from discord.ext import commands
from unittest.mock import MagicMock

from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import UsagiConfig, UsagiSaveRoles
from usagiBot.src.UsagiUtils import get_embed


def get_all_bot_cogs(ctx: discord.AutocompleteContext):
    return ctx.bot.cogs


class Main(commands.Cog):
    def __init__(self, bot):
        pass

    @commands.slash_command(name="help", description="Show help for commands")
    @discord.commands.option(
        name="module",
        description="",
        autocomplete=get_all_bot_cogs,
        required=True,
    )
    async def help_command(
        self,
        ctx,
        module,
    ) -> None:
        module = ctx.bot.cogs.get(module, None)
        if module is None:
            return await ctx.respond(
                embed=get_embed(
                    title="There is no module with that name.",
                    color=discord.Color.red(),
                )
            )

        try:
            module.cog_check(ctx)
        except UsagiModuleDisabledError:
            return await ctx.respond(
                embed=get_embed(
                    title="This module is disabled", color=discord.Color.red()
                )
            )

        types = {
            discord.ext.commands.core.Command: "Default commands",
            discord.commands.core.SlashCommand: "Slash commands",
            discord.commands.core.MessageCommand: "Message commands",
            discord.commands.core.UserCommand: "User commands",
            discord.commands.SlashCommandGroup: "Slash command group",
        }

        title = f"**{module.qualified_name}**"
        embed = get_embed(
            title=title,
        )

        commands_dict = {}
        for command in module.get_commands():
            command_dict = {
                "name": command.name,
                "description": command.description,
                "set_up": True,
                "channel_id": None,
            }
            if command.parent:
                command_tag = command.parent.__original_kwargs__.get("command_tag")
            else:
                command_tag = command.__original_kwargs__.get("command_tag")
            if command_tag:
                config = await UsagiConfig.get(
                    guild_id=ctx.guild.id, command_tag=command_tag
                )
                if not config:
                    command_dict["set_up"] = False
                else:
                    command_dict["channel_id"] = config.generic_id

            # for check in command.checks:
            #     await check(ctx)

            command_type = types.get(type(command))
            command_list = commands_dict.setdefault(command_type, [])
            command_list.append(command_dict)

        for item, value in commands_dict.items():
            embed.add_field(name=f"_ _\n**{item}**", value="_ _")
            for command in value:
                value = ""
                if command["set_up"]:
                    if command["channel_id"]:
                        value += f"Configured - <#{command['channel_id']}>\n"
                    else:
                        value += "Configured - No needed\n"
                else:
                    value += "Configured - <:redThick:874767320915005471>\n"
                value += command["description"]
                embed.add_field(name=command["name"], value=value)
        for field in embed.fields:
            print(field.name, field.value)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="save_roles",
        description="Toggle saving roles on user leave guild",
        command_tag="save_roles_on_leave",
    )
    async def save_roles_on_leave(self, ctx) -> None:
        saving = await UsagiSaveRoles.get(guild_id=ctx.guild.id)
        if saving is None:
            await UsagiSaveRoles.create(guild_id=ctx.guild.id, saving_roles=True)
            return await ctx.respond(
                embed=get_embed(
                    title="Enabled saving roles on member leave.",
                    color=discord.Color.green(),
                )
            )
        else:
            if saving.saving_roles:
                await UsagiSaveRoles.update(id=saving.id, saving_roles=False)
                return await ctx.respond(
                    embed=get_embed(
                        title="Disabled saving roles on member leave.",
                        color=discord.Color.green(),
                    )
                )
            else:
                await UsagiSaveRoles.update(id=saving.id, saving_roles=True)
                return await ctx.respond(
                    embed=get_embed(
                        title="Enabled saving roles on member leave.",
                        color=discord.Color.green(),
                    )
                )


def setup(bot):
    bot.add_cog(Main(bot))
