from bin.functions import get_member_by_all


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



async def buy_server_boost(self, ctx, data = None):
    return 'Жесть ты кадр конечно, гц гц, <@290166276796448768> у нас тут пчел нарисовался, бусты купить хочет'