from datetime import datetime
from typing import List

import discord
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup

from usagiBot.src.UsagiChecks import check_correct_channel_command, check_member_is_moder, is_owner
from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import (
    UsagiConfig,
    UsagiSaveRoles,
    UsagiAutoRoles,
    UsagiAutoRolesData,
    UsagiTimer,
    UsagiLanguage
)
from usagiBot.src.UsagiUtils import get_embed
from pycord18n.extension import _


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

    @tasks.loop(minutes=10)
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

    @commands.slash_command(
        name="help",
        name_localizations={"ru": "помощь"},
        description="Show help for commands",
        description_localizations={"ru": "Показать помощь по командам"},
    )
    @discord.commands.option(
        name="module",
        name_localizations={"ru": "модуль"},
        description="",
        autocomplete=get_all_bot_cogs,
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
                    title=_("There is no module with that name"),
                    color=discord.Color.red(),
                ),
                ephemeral=True
            )

        try:
            module.cog_check(ctx)
        except UsagiModuleDisabledError:
            return await ctx.respond(
                embed=get_embed(
                    title=_("This module is disabled"), color=discord.Color.red()
                ),
                ephemeral=True
            )

        types = {
            discord.ext.commands.core.Command: _("Default commands"),
            discord.commands.core.SlashCommand: _("Slash commands"),
            discord.commands.core.MessageCommand: _("Message commands"),
            discord.commands.core.UserCommand: _("User commands"),
        }

        title = f"**{module.qualified_name}**"
        embed = get_embed(
            title=title,
        )

        commands_dict = {}
        for command in module.walk_commands():
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

            if isinstance(command, discord.commands.SlashCommandGroup):
                continue

            command_type = types.get(type(command))
            command_list = commands_dict.setdefault(command_type, [])
            command_list.append(command_dict)

        for item, value in commands_dict.items():
            embed.add_field(name=f"_ _\n**{item}**", value="_ _", inline=False)
            for command in value:
                value = ""
                if command.get("set_up", None):
                    if command.get("channel_id", None):
                        value += _("Configured").format(channel_id=command["channel_id"])
                else:
                    value += _("Configured - Nope")
                value += command["description"]
                embed.add_field(name=command["name"], value=value, inline=True)
        await ctx.respond(embed=embed, ephemeral=True)

    timer_group = SlashCommandGroup(
        name="timer",
        name_localizations={"ru": "таймер"},
        description="Set countdown timer for any event!",
        description_localizations={"ru": "Поставить таймер отсчёта"},
        checks=[
            check_member_is_moder
        ],
    )

    @timer_group.command(name="add", description="Add timer to date")
    @discord.commands.option(
        name="date",
        name_localizations={"ru": "дата"},
        description="Enter date in `d.m.Y H:M:S` format.",
        description_localizations={"ru": "Введите дату в формате `д.м.Г Ч:М:С`"},
    )
    async def add_timer(
            self,
            ctx,
            channel: discord.VoiceChannel,
            date: str,
    ) -> None:
        try:
            datetime_obj = datetime.strptime(date, "%m.%d.%Y %H:%M:%S")
        except ValueError or KeyError:
            return await ctx.respond(
                embed=get_embed(
                    title=_("Time data does not match format").format(date),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        timer = await UsagiTimer.get(guild_id=ctx.guild.id, channel_id=channel.id)
        response = _("Added new timer")
        if timer:
            await UsagiTimer.update(id=timer.id, date=datetime_obj)
            response = _("Changed timer")
        else:
            await UsagiTimer.create(guild_id=ctx.guild.id, channel_id=channel.id, date=datetime_obj)
        await ctx.respond(
            embed=get_embed(
                title=response,
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @timer_group.command(
        name="remove",
        name_localizations={"ru": "удалить"},
        description="Remove timer.",
        description_localizations={"ru": "Удалить таймер."},
    )
    @discord.commands.option(
        name="timer",
        name_localizations={"ru": "таймер"},
        description="Select timer to remove",
        description_localizations={"ru": "Выберите таймер, который надо удалить."},
        autocomplete=get_timers,
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
                    title=_("There is no timer in that channel"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        await UsagiTimer.delete(id=old_timer.id)
        await ctx.respond(
            embed=get_embed(
                title=_("Successfully removed"),
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @commands.slash_command(
        name="save_roles",
        name_localizations={"ru": "сохранить_роли"},
        description="Toggle saving roles on user leave guild",
        description_localizations={"ru": "Авто сохранение ролей пользователя при выходе с сервера."},
        command_tag="save_roles_on_leave",
    )
    @check_correct_channel_command()
    @commands.check(check_member_is_moder)
    async def save_roles_on_leave(self, ctx) -> None:
        saving = await UsagiSaveRoles.get(guild_id=ctx.guild.id)
        if saving is None:
            await UsagiSaveRoles.create(guild_id=ctx.guild.id, saving_roles=True)
            return await ctx.respond(
                embed=get_embed(
                    title=_("Enabled saving roles on member leave"),
                    color=discord.Color.green(),
                )
            )
        else:
            if saving.saving_roles:
                await UsagiSaveRoles.update(id=saving.id, saving_roles=False)
                return await ctx.respond(
                    embed=get_embed(
                        title=_("Disabled saving roles on member leave"),
                        color=discord.Color.green(),
                    )
                )
            else:
                await UsagiSaveRoles.update(id=saving.id, saving_roles=True)
                return await ctx.respond(
                    embed=get_embed(
                        title=_("Enabled saving roles on member leave"),
                        color=discord.Color.green(),
                    )
                )

    auto_roles = SlashCommandGroup(
        name="auto_role",
        name_localizations={"ru": "авто_роли"},
        description="Give your members roles by reacting on message!",
        description_localizations={"ru": "Раздавайте пользователям роли, за их реакции под сообщениями!"},
        checks=[
            check_member_is_moder
        ],
    )
    edit_roles = auto_roles.create_subgroup(
        name="edit",
        name_localizations={"ru": "изменить"},
        description="Change your auto roles!",
        description_localizations={"ru": "Изменяйте ваши авто роли!"},
    )

    @auto_roles.command(
        name="create",
        name_localizations={"ru": "создать"},
        description="Create a message with auto roles",
        description_localizations={"ru": "Создать сообщение для авто ролей."},
    )
    @discord.commands.option(
        name="channel",
        name_localizations={"ru": "канал"},
        description="Channel to spawn message with roles",
        description_localizations={"ru": "Канал где создать сообщение для авто ролей."},
    )
    @discord.commands.option(
        name="name",
        name_localizations={"ru": "имя"},
        description="Choose a name for message",
        description_localizations={"ru": "Имя сообщения."},
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
            embed=get_embed(title=_("Done"), color=discord.Color.green()), ephemeral=True
        )

    @auto_roles.command(
        name="remove",
        name_localizations={"ru": "удалить"},
        description="Remove a message with auto roles",
        description_localizations={"ru": "Удалить сообщение с авто ролями."},
    )
    @discord.commands.option(
        name="message",
        name_localizations={"ru": "сообщение"},
        description="Pick which message remove",
        description_localizations={"ru": "Выбрать какое сообщение удалить."},
        autocomplete=get_auto_role_messages,
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
                    title=_("This is not a message with auto role"),
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
                    title=_("Cannot remove original message"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        await ctx.respond(
            embed=get_embed(title=_("Removed"), color=discord.Color.green()), ephemeral=True
        )

    @auto_roles.command(
        name="add",
        name_localizations={"ru": "добавить"},
        description="Add reaction role to your message",
        description_localizations={"ru": "Добавить реакцию на сообщение"},
    )
    @discord.commands.option(
        name="message",
        name_localizations={"ru": "сообщение"},
        description="Pick for which message add role",
        description_localizations={"ru": "Выберите для какого сообщения добавить роль."},
        autocomplete=get_auto_role_messages,
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a role to add",
        description_localizations={"ru": "Выберите роль"},
    )
    @discord.commands.option(
        name="emoji",
        name_localizations={"ru": "емоджи"},
        description="Pick a emoji for role",
        description_localizations={"ru": "Выберите эмоджи для роли"},
    )
    @discord.commands.option(
        name="description",
        name_localizations={"ru": "описание"},
        description="Add description",
        description_localizations={"ru": "Добавьте описание"},
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
                    title=_("This is not a message with auto role"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.respond(
                embed=get_embed(
                    title=_("From message was removed all ebmeds"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        if len(msg.reactions) == 20:
            return await ctx.respond(
                embed=get_embed(
                    title=_("This message already had 20 reactions"),
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
                            title=_("This role or emoji already used"),
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
            embed=get_embed(title=_("Added"), color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(
        name="remove",
        name_localizations={"ru": "удалить"},
        description="Remove reaction role from your message",
        description_localizations={"ru": "Удалить роль из сообщение."},
    )
    @discord.commands.option(
        name="message",
        name_localizations={"ru": "сообщение"},
        description="Pick from which message remove role",
        description_localizations={"ru": "Выберите из какого сообщения удалить роль."},
        autocomplete=get_auto_role_messages,
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Pick a role to remove",
        description_localizations={"ru": "Выберите роль, которую надо удалить."},
        autocomplete=get_roles_from_message,
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
                    title=_("This is not a message with auto role"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.respond(
                embed=get_embed(
                    title=_("From message was removed all ebmeds"),
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
            embed=get_embed(title=_("Removed"), color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(
        name="role",
        name_localizations={"ru": "роль"},
        description="Edit reaction role.",
        description_localizations={"ru": "Изменить роль в авто сообщении."},
    )
    @discord.commands.option(
        name="message",
        name_localizations={"ru": "сообщение"},
        description="Pick for which message edit role.",
        description_localizations={"ru": "Выберите сообщение"},
        autocomplete=get_auto_role_messages,
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Select a role to change.",
        description_localizations={"ru": "Выберите роль, которую надо изменить."},
        autocomplete=get_roles_from_message,
    )
    @discord.commands.option(
        name="new_role",
        name_localizations={"ru": "новая_роль"},
        description="Enter new role.",
        description_localizations={"ru": "Выберите новую роль."},
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
                    title=_("This is not a message with auto role"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.send_followup(
                embed=get_embed(
                    title=_("From message was removed all ebmeds"),
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
                    title=_("This role already used"),
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
                    title=_("Cannot edit original message"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        await UsagiAutoRolesData.update(
            id=new_entity.id,
            role_id=new_role.id,
        )
        await ctx.send_followup(
            embed=get_embed(title=_("Role edited"), color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(
        name="emoji",
        name_localizations={"ru": "емоджи"},
        description="Edit reaction emoji.",
        description_localizations={"ru": "Изменить емоджи, в авто сообщении."},
    )
    @discord.commands.option(
        name="message",
        name_localizations={"ru": "сообщение"},
        description="Pick for which message edit emoji",
        description_localizations={"ru": "Выберите сообщение, в котором надо изменить."},
        autocomplete=get_auto_role_messages,
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Select a role to change.",
        description_localizations={"ru": "Выберите роль, для которой надо изменить."},
        autocomplete=get_roles_from_message,
    )
    @discord.commands.option(
        name="new_emoji",
        name_localizations={"ru": "новый_емоджи"},
        description_localizations={"ru": "Выберите новую эмоджи."},
        description="Enter new emoji",
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
                    title=_("This is not a message with auto role"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.send_followup(
                embed=get_embed(
                    title=_("From message was removed all ebmeds"),
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
                    title=_("This emoji already used"),
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
                    title=_("Cannot edit original message"),
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
            embed=get_embed(title=_("Emoji edited"), color=discord.Color.green()), ephemeral=True
        )

    @edit_roles.command(
        name="description",
        name_localizations={"ru": "описание"},
        description="Edit reaction description.",
        description_localizations={"ru": "Изменить описание."},
    )
    @discord.commands.option(
        name="message",
        name_localizations={"ru": "сообщение"},
        description="Pick for which message edit description.",
        description_localizations={"ru": "Выберите сообщение, в котором надо изменить."},
        autocomplete=get_auto_role_messages,
    )
    @discord.commands.option(
        name="role",
        name_localizations={"ru": "роль"},
        description="Select a role to change.",
        description_localizations={"ru": "Выберите роль, для которой надо изменить."},
        autocomplete=get_roles_from_message,
    )
    @discord.commands.option(
        name="new_description",
        name_localizations={"ru": "новое_описание"},
        description="Enter new description.",
        description_localizations={"ru": "Новое описание."},
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
                    title=_("This is not a message with auto role"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        channel = await ctx.guild.fetch_channel(role_data["channel_id"])
        msg = await channel.fetch_message(int(message_id))
        if len(msg.embeds) == 0:
            return await ctx.send_followup(
                embed=get_embed(
                    title=_("From message was removed all ebmeds"),
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
                    title=_("Cannot edit original message"),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        await UsagiAutoRolesData.update(
            id=new_entity.id,
            description=new_description,
        )
        await ctx.send_followup(
            embed=get_embed(title=_("Description edited"), color=discord.Color.green()), ephemeral=True
        )

    @commands.slash_command(
        name="lang",
        name_localizations={"ru": "язык"},
        description="Set language for bot",
        description_localizations={"ru": "Выбрать язык для бота."},
    )
    @discord.commands.option(
        name="lang",
        name_localizations={"ru": "язык"},
        description="",
        choices=["ru", "en"],
    )
    async def change_lang(
            self,
            ctx,
            lang: str,
    ) -> None:
        user = await UsagiLanguage.get(user_id=ctx.author.id)

        if user is None:
            await UsagiLanguage.create(user_id=ctx.author.id, lang=lang)
        else:
            await UsagiLanguage.update(id=user.id, lang=lang)

        self.bot.language.setdefault(ctx.author.id, "")
        self.bot.language[ctx.author.id] = lang

        await ctx.respond(
            embed=get_embed(
                title=_("Changed your language").format(lang=lang),
                color=discord.Color.green(),
            ),
            ephemeral=True
        )


def setup(bot):
    bot.add_cog(Main(bot))
