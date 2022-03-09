
async def buy_based_apple(ctx):
    return 'БАХНУЛ БАЗОВОГО ЯБЛОЧКА НА ТРОИХ И СИДИТ КАЙФУЕТ'

async def send_wesdos_nahui(ctx):
    guild = await ctx.bot.fetch_guild(858053936313008129)
    member = await guild.fetch_member(332882488961662978)
    channel = await guild.fetch_channel(858053937008214018)
    await channel.send(f'{member.mention}, ИДИ НАХУЙ!')
    return 'Послал Весдоса нахуй'



async def buy_server_boost(ctx):
    return 'Жесть ты кадр конечно, гц гц, <@290166276796448768> у нас тут пчел нарисовался, бусты купить хочет'