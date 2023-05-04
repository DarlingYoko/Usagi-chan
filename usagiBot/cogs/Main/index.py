from datetime import datetime
from typing import List

import discord
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup

from usagiBot.src.UsagiChecks import check_correct_channel_command, check_member_is_moder
from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import UsagiConfig, UsagiSaveRoles, UsagiAutoRoles, UsagiAutoRolesData, UsagiTimer
from usagiBot.src.UsagiUtils import get_embed


def get_all_bot_cogs(ctx: discord.AutocompleteContext):
    return ctx.bot.cogs


async def get_auto_role_messages(
        ctx: discord.AutocompleteContext,
) -> List[discord.OptionChoice]:
    """
    Returns a list of command tags.
    """
    auto_roles = ctx.bot.auto_roles.get(ctx.interaction.guild_id, {})
    names = [
        discord.OptionChoice(name=value["name"], value=message_id)
        for message_id, value in auto_roles.items()
    ]
    return names


async def get_timers(
        ctx: discord.AutocompleteContext,
) -> List[discord.OptionChoice]:
    """
    Returns a list of command tags.
    """
    timers = await UsagiTimer.get_all_by(guild_id=ctx.interaction.guild_id)
    guild = ctx.bot.get_guild(ctx.interaction.guild_id)
    timer_names = []
    for timer in timers:
        channel = await guild.fetch_channel(timer.channel_id)
        timer_names.append(discord.OptionChoice(name=channel.name, value=str(timer.channel_id)))

    return timer_names


async def get_roles_from_message(ctx: discord.AutocompleteContext) -> List[discord.OptionChoice]:
    picked_message = ctx.options["message"]
    role_data = await UsagiAutoRolesData.get_all_by(message_id=picked_message)
    roles = list(map(lambda role: ctx.interaction.guild.get_role(role.role_id), role_data))
    roles = [
        discord.OptionChoice(name=role.name, value=str(role.id))
        for role in roles
    ]
    return roles


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_timer.start()

    @tasks.loop(minutes=30)
    async def update_timer(self):
        timers = await UsagiTimer.get_all()
        time_now = datetime.now()

        for timer in timers:
            guild = await self.bot.fetch_guild(timer.guild_id)
            channel = await guild.fetch_channel(timer.channel_id)
            delta = timer.date - time_now
            s = delta.seconds
            hours, remainder = divmod(s, 3600)
            minutes, seconds = divmod(remainder, 60)
            time = ""
            if delta.days:
                time += f"{delta.days} d."
            time += f" {hours} h. {minutes} m."
            await channel.edit(name=time, reason="Update timer.")

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
                ),
                ephemeral=True
            )

        try:
            module.cog_check(ctx)
        except UsagiModuleDisabledError:
            return await ctx.respond(
                embed=get_embed(
                    title="This module is disabled", color=discord.Color.red()
                ),
                ephemeral=True
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
                embed.add_field(name=command["name"], value=value, inline=False)
        await ctx.respond(embed=embed, ephemeral=True)

    timer_group = SlashCommandGroup(
        name="timer",
        description="Set countdown timer for any event!",
        checks=[
            check_member_is_moder
        ],
    )

    @timer_group.command(name="add", description="Add timer to date")
    @discord.commands.option(
        name="date",
        description="Enter date in `%m.%d.%Y %H:%M:%S` format.",
        required=True,
    )
    async def add_timer(
            self,
            ctx,
            channel: discord.VoiceChannel,
            date: str,
    ) -> None:
        try:
            datetime_obj = datetime.strptime(date, "%m.%d.%Y %H:%M:%S")
        except ValueError:
            return await ctx.respond(
                embed=get_embed(
                    title=f"Time data `{date}` does not match format `%m.%d.%Y %H:%M:%S`",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        timer = await UsagiTimer.get(guild_id=ctx.guild.id, channel_id=channel.id)
        response = "Added new timer"
        if timer:
            await UsagiTimer.update(id=timer.id, date=datetime_obj)
            response = "Changed timer"
        else:
            await UsagiTimer.create(guild_id=ctx.guild.id, channel_id=channel.id, date=datetime_obj)
        await ctx.respond(
            embed=get_embed(
                title=response,
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @timer_group.command(name="remove", description="Add timer to date")
    @discord.commands.option(
        name="timer",
        description="Select timer to remove",
        autocomplete=get_timers,
        required=True,
    )
    async def remove_timer(
            self,
            ctx,
            timer: str,
    ) -> None:
        old_timer = await UsagiTimer.get(guild_id=ctx.guild.id, channel_id=int(timer))
        if old_timer is None:
            return await ctx.respond(
                embed=get_embed(
                    title=f"There is no timer in that channel",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        await UsagiTimer.delete(id=old_timer.id)
        await ctx.respond(
            embed=get_embed(
                title="Successfully removed",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @commands.slash_command(
        name="save_roles",
        description="Toggle saving roles on user leave guild",
        command_tag="save_roles_on_leave",
    )
    @check_correct_channel_command()
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

    auto_roles = SlashCommandGroup(
        name="auto_role",
        description="Give your members roles by reacting on message!",
        checks=[
            check_member_is_moder
        ],
    )
    edit_roles = auto_roles.create_subgroup(
        name="edit",
        description="Give your members roles by reacting on message!",
    )

    @auto_roles.command(name="create", description="Create a message with auto roles")
    @discord.commands.option(
        name="channel",
        description="Channel to spawn message with roles",
        required=True,
    )
    @discord.commands.option(
        name="name",
        description="Choose a name for message",
        required=True,
    )
    async def create_auto_role_message(
            self,
            ctx,
            channel: discord.TextChannel,
            name: str,
    ) -> None:
        msg = await channel.send(embed=get_embed(title=name))

        await UsagiAutoRoles.create(
            guild_id=ctx.guild.id,
            channel_id=channel.id,
            message_id=str(msg.id),
            name=name,
        )
        guild = ctx.bot.auto_roles.setdefault(ctx.guild.id, {})
        guild[str(msg.id)] = {
            "name": name,
            "channel_id": channel.id
        }
        await ctx.respond(
            embed=get_embed(title="Done", color=discord.Color.green()), ephemeral=True
        )

    @auto_roles.command(name="remove", description="Remove a message with auto roles")
    @discord.commands.option(
        name="message",
        description="Pick for which message add role",
        autocomplete=get_auto_role_messages,
        required=True,
    )
    async def remove_auto_role_message(
            self,
            ctx,
            message: str,
    ) -> None:
        auto_roles = ctx.bot.auto_roles.get(ctx.guild_id, {})
        message_id = message
        role_data = auto_roles.get(message_id, None)
        if role_data is None:
            return await ctx.respond(
                embed=get_embed(
                    title="This is not a message with auto role",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))

        try:
            await msg.delete(reason=f"Remove by slash command {ctx.author.name}")
            await UsagiAutoRolesData.delete(message_id=message_id)
            await UsagiAutoRoles.delete(message_id=message_id)
        except discord.errors.Forbidden or discord.errors.NotFound:
            return await ctx.send_followup(
                embed=get_embed(
                    title="Cannot remove original message",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        await ctx.respond(
            embed=get_embed(title="Removed", color=discord.Color.green()), ephemeral=True
        )

    @auto_roles.command(name="add", description="Add reaction role to your message")
    @discord.commands.option(
        name="message",
        description="Pick for which message add role",
        autocomplete=get_auto_role_messages,
        required=True,
    )
    @discord.commands.option(
        name="role",
        description="Pick a role to add",
        required=True,
    )
    @discord.commands.option(
        name="emoji",
        description="Pick a emoji for role",
        required=True,
    )
    @discord.commands.option(
        name="description",
        description="Add description (optional)",
        required=True,
    )
    async def add_reaction_role(
            self,
            ctx,
            message: str,
            role: discord.Role,
            emoji: discord.Emoji,
            description: str,
    ):
        auto_roles = ctx.bot.auto_roles.get(ctx.guild_id, {})
        message_id = message
        role_data = auto_roles.get(message_id, None)
        if role_data is None:
            return await ctx.respond(
                embed=get_embed(
                    title="This is not a message with auto role",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.respond(
                embed=get_embed(
                    title="From message was removed all ebmeds. Pls recreate it.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        if len(msg.reactions) == 0:
            return await ctx.respond(
                embed=get_embed(
                    title="This message already had 20 reactions.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        payload = await UsagiAutoRolesData.get_all_by(message_id=message_id)
        text = ""
        counter = 1
        if payload is not None:
            for entity in payload:
                if entity.role_id == role.id or entity.emoji_id == emoji.id:
                    return await ctx.respond(
                        embed=get_embed(
                            title="This role or emoji already used.",
                            color=discord.Color.red()
                        ),
                        ephemeral=True
                    )
                payload_emoji = await ctx.guild.fetch_emoji(entity.emoji_id)
                text += f"{counter}. <@&{entity.role_id}> – {entity.description} – {payload_emoji}\n"
                counter += 1

        text += f"{counter}. {role.mention} – {description} – {emoji}"
        embed = get_embed(
            title=role_data["name"],
            description=text
        )

        await msg.edit(embed=embed)
        await msg.add_reaction(emoji)

        await UsagiAutoRolesData.create(
            message_id=message_id,
            role_id=role.id,
            emoji_id=emoji.id,
            description=description,
        )

        await ctx.respond(
            embed=get_embed(title="Added", color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(name="remove", description="Remove reaction role from your message")
    @discord.commands.option(
        name="message",
        description="Pick from which message remove role",
        autocomplete=get_auto_role_messages,
        required=True,
    )
    @discord.commands.option(
        name="role",
        description="Pick a role to remove",
        autocomplete=get_roles_from_message,
        required=True,
    )
    async def remove_reaction_role(
            self,
            ctx,
            message: str,
            role: str,
    ):
        auto_roles = ctx.bot.auto_roles.get(ctx.guild_id, {})
        message_id = message
        role_data = auto_roles.get(message_id, None)
        if role_data is None:
            return await ctx.respond(
                embed=get_embed(
                    title="This is not a message with auto role",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.respond(
                embed=get_embed(
                    title="From message was removed all ebmeds. Pls recreate it.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        payload = await UsagiAutoRolesData.get_all_by(message_id=message_id)
        text = ""
        old_emoji = None
        for counter, entity in enumerate(payload, start=1):
            if entity.role_id == int(role):
                old_emoji = await ctx.guild.fetch_emoji(entity.emoji_id)
                continue
            payload_emoji = await ctx.guild.fetch_emoji(entity.emoji_id)
            text += f"{counter}. <@&{entity.role_id}> – {entity.description} – {payload_emoji}\n"
        embed = get_embed(
            title=role_data["name"],
            description=text
        )

        await msg.edit(embed=embed)
        await msg.clear_reaction(old_emoji)
        await UsagiAutoRolesData.delete(
            message_id=message_id,
            role_id=int(role),
        )

        await ctx.respond(
            embed=get_embed(title="Removed", color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(name="role", description="Edit reaction role.")
    @discord.commands.option(
        name="message",
        description="Pick for which message edit role.",
        autocomplete=get_auto_role_messages,
        required=True,
    )
    @discord.commands.option(
        name="role",
        description="Select a role to change.",
        autocomplete=get_roles_from_message,
        required=True,
    )
    @discord.commands.option(
        name="new_role",
        description="Enter new role.",
        required=True,
    )
    async def edit_role_reaction_role(
            self,
            ctx,
            message: str,
            role: str,
            new_role: discord.Role,
    ):
        await ctx.defer(ephemeral=True)
        auto_roles = ctx.bot.auto_roles.get(ctx.guild_id, {})
        message_id = message
        role_data = auto_roles.get(message_id, None)
        if role_data is None:
            return await ctx.send_followup(
                embed=get_embed(
                    title="This is not a message with auto role",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.send_followup(
                embed=get_embed(
                    title="From message was removed all ebmeds. Pls recreate it.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        payload = await UsagiAutoRolesData.get_all_by(message_id=message_id)
        text = ""
        new_entity = next((entity for entity in payload if entity.role_id == new_role.id), None)
        if new_entity is not None:
            return await ctx.send_followup(
                embed=get_embed(
                    title="This role already used.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        for counter, entity in enumerate(payload, start=1):
            if entity.role_id == int(role):
                new_entity = entity
                entity.role_id = new_role.id
            payload_emoji = await ctx.guild.fetch_emoji(entity.emoji_id)
            text += f"{counter}. <@&{entity.role_id}> – {entity.description} – {payload_emoji}\n"
        embed = get_embed(
            title=role_data["name"],
            description=text
        )
        try:
            await msg.edit(embed=embed)
        except discord.errors.Forbidden:
            return await ctx.send_followup(
                embed=get_embed(
                    title="Cannot edit original message",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        await UsagiAutoRolesData.update(
            id=new_entity.id,
            role_id=new_role.id,
        )
        await ctx.send_followup(
            embed=get_embed(title="Role edited", color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(name="emoji", description="Edit reaction emoji.")
    @discord.commands.option(
        name="message",
        description="Pick for which message edit emoji",
        autocomplete=get_auto_role_messages,
        required=True,
    )
    @discord.commands.option(
        name="role",
        description="Select a role to change.",
        autocomplete=get_roles_from_message,
        required=True,
    )
    @discord.commands.option(
        name="new_emoji",
        description="Enter new emoji",
        required=True,
    )
    async def edit_emoji_reaction_role(
            self,
            ctx,
            message: str,
            role: str,
            new_emoji: discord.Emoji,
    ):
        await ctx.defer(ephemeral=True)
        auto_roles = ctx.bot.auto_roles.get(ctx.guild_id, {})
        message_id = message
        role_data = auto_roles.get(message_id, None)
        if role_data is None:
            return await ctx.send_followup(
                embed=get_embed(
                    title="This is not a message with auto role",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.send_followup(
                embed=get_embed(
                    title="From message was removed all ebmeds. Pls recreate it.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        payload = await UsagiAutoRolesData.get_all_by(message_id=message_id)
        text = ""
        old_emoji = None
        new_entity = next((entity for entity in payload if entity.emoji_id == new_emoji.id), None)
        if new_entity is not None:
            return await ctx.send_followup(
                embed=get_embed(
                    title="This emoji already used.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        for counter, entity in enumerate(payload, start=1):
            if entity.role_id == int(role):
                new_entity = entity
                old_emoji = entity.emoji_id
                entity.emoji_id = new_emoji.id
            payload_emoji = await ctx.guild.fetch_emoji(entity.emoji_id)
            text += f"{counter}. <@&{entity.role_id}> – {entity.description} – {payload_emoji}\n"
        embed = get_embed(
            title=role_data["name"],
            description=text
        )
        try:
            await msg.edit(embed=embed)
            await msg.add_reaction(new_emoji)
            payload_emoji = await ctx.guild.fetch_emoji(old_emoji)
            await msg.clear_reaction(payload_emoji)
        except discord.errors.Forbidden:
            return await ctx.send_followup(
                embed=get_embed(
                    title="Cannot edit original message",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        except discord.errors.NotFound:
            pass

        await UsagiAutoRolesData.update(
            id=new_entity.id,
            emoji_id=new_emoji.id,
        )
        await ctx.send_followup(
            embed=get_embed(title="Emoji edited", color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(name="description", description="Edit reaction description.")
    @discord.commands.option(
        name="message",
        description="Pick for which message edit description.",
        autocomplete=get_auto_role_messages,
        required=True,
    )
    @discord.commands.option(
        name="role",
        description="Select a role to change.",
        autocomplete=get_roles_from_message,
        required=True,
    )
    @discord.commands.option(
        name="new_description",
        description="Enter new description.",
        required=True,
    )
    async def edit_description_reaction_role(
            self,
            ctx,
            message: str,
            role: str,
            new_description: str,
    ):
        await ctx.defer(ephemeral=True)
        auto_roles = ctx.bot.auto_roles.get(ctx.guild_id, {})
        message_id = message
        role_data = auto_roles.get(message_id, None)
        if role_data is None:
            return await ctx.send_followup(
                embed=get_embed(
                    title="This is not a message with auto role",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.send_followup(
                embed=get_embed(
                    title="From message was removed all ebmeds. Pls recreate it.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        payload = await UsagiAutoRolesData.get_all_by(message_id=message_id)
        text = ""
        new_entity = None
        for counter, entity in enumerate(payload, start=1):
            if entity.role_id == int(role):
                new_entity = entity
                entity.description = new_description
            payload_emoji = await ctx.guild.fetch_emoji(entity.emoji_id)
            text += f"{counter}. <@&{entity.role_id}> – {entity.description} – {payload_emoji}\n"
        embed = get_embed(
            title=role_data["name"],
            description=text
        )
        try:
            await msg.edit(embed=embed)
        except discord.errors.Forbidden:
            return await ctx.send_followup(
                embed=get_embed(
                    title="Cannot edit original message",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        await UsagiAutoRolesData.update(
            id=new_entity.id,
            description=new_description,
        )
        await ctx.send_followup(
            embed=get_embed(title="Description edited", color=discord.Color.green()), ephemeral=True
        )


def setup(bot):
    bot.add_cog(Main(bot))
