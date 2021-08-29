import discord
from discord.ext import commands


class UserConverter(commands.Converter):
    async def convert(self, ctx, argument):
        member = discord.utils.find(lambda m: m.display_name.lower().startswith(argument.lower()), ctx.guild.members)
        if not member:
            raise commands.BadArgument
        return member


class ColorConverter(commands.Converter):
    async def convert(self, ctx, color):
        if '#' in color:
            color = color[1:]
        try:
            colorHex = int(color, 16)
        except ValueError:
            raise commands.BadArgument
        return colorHex


class RoleConverter(commands.Converter):
    async def convert(self, ctx, role_id):
        user_role = None
        for role in ctx.author.roles:
            if str(role.id) in role_id:
                user_role = role
        if user_role:
            return user_role
        else:
            await ctx.send(f'{ctx.author.mention}, Это не твоя роль, бааака!')
            raise Exception
