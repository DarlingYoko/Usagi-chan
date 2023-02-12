from typing import List

import discord
from discord import OptionChoice

from usagiBot.db.models import UsagiUnicRoles


async def get_user_roles(ctx: discord.AutocompleteContext) -> List:
    """
    Returns a list of user roles.
    """
    guild = ctx.interaction.guild
    role_ids = await UsagiUnicRoles.get_all_by(
        guild_id=guild.id,
        user_id=ctx.interaction.user.id,
    )
    if not role_ids:
        return []

    role_ids = list(map(lambda x: x.role_id, role_ids))
    all_roles = await guild.fetch_roles()
    roles = list(filter(lambda x: x.id in role_ids, all_roles))
    role_names = list(map(lambda x: OptionChoice(name=x.name, value=str(x.id)), roles))
    return role_names


async def get_user_role(ctx, role_id):
    role_id = int(role_id)
    user_roles = await get_user_roles(ctx)
    user_role_ids = list(map(lambda x: int(x.value), user_roles))
    if role_id not in user_role_ids:
        await ctx.respond("It's not your role or you didn't create it", ephemeral=True)
        return None
    role = ctx.guild.get_role(role_id)
    return role
