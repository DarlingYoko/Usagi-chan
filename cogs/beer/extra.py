import discord
from random import choice
from datetime import timedelta



async def buy_based_apple(self, ctx, data = None):
    return 'БАХНУЛ БАЗОВОГО ЯБЛОЧКА НА ТРОИХ И СИДИТ КАЙФУЕТ'

async def send_wesdos_nahui(self, ctx, data = None):
    guild = await self.bot.fetch_guild(self.bot.config['data']['guild_id'])
    member = await guild.fetch_member(332882488961662978)
    channel = await guild.fetch_channel(self.bot.config['channel']['main'])
    await channel.send(f'{member.mention}, ИДИ НАХУЙ!')
    return 'Послал Весдоса нахуй'

async def anon_send_nahui(self, ctx, member):
    guild = await self.bot.fetch_guild(self.bot.config['data']['guild_id'])
    channel = await guild.fetch_channel(self.bot.config['channel']['main'])
    await channel.send(f'{member.mention}, ИДИ НАХУЙ!')
    return 'Послал пользователя нахуй'

async def pidors_send_nahui(self, ctx, member):
    guild = await self.bot.fetch_guild(self.bot.config['data']['guild_id'])
    channel = await guild.fetch_channel(self.bot.config['channel']['main'])
    await channel.send(f'<@&950668415402651718>, ИДИТЕ НАХУЙ!')
    return 'Послал пользователя нахуй'



async def ban_casino(self, ctx, data = None):
    guild = await self.bot.fetch_guild(self.bot.config['data']['guild_id'])
    members = await guild.fetch_members(limit=None).flatten()
    member = choice(members)
    try:
        await member.timeout_for(duration=timedelta(hours=3), reason='Выйграл в рулетку')
    except discord.ext.commands.BotMissingPermissions:
        pass
    await ctx.send(f'{member.mention}, Ты выйграл в рулетку!! ЮХУУ, мои поздравления! Отбывай в муте на 1 час, приятно иметь с тобой дела.')
    return 'Заролил рулетку на рандомный бан'