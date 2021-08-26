import discord
from discord.ext import commands
from bin.functions import get_config, check_str_in_list


class Technical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name = 'эмодзи', brief='Добавление нового эмодзи')
    #@is_channel(config['channel'].getint('mp'))
    async def create_new_emoji(self, ctx, name: str):

        if not ctx.message.attachments:
            raise commands.BadArgument

        image = None

        for attachment in ctx.message.attachments:
            if check_str_in_list(attachment.content_type, ['jpg', 'png', 'gif', 'jpeg']):
                image = await attachment.read()

        if not image:
            raise commands.BadArgument

        try:
            emoji = await ctx.guild.create_custom_emoji(name = name, image = image)
            await ctx.send(f'{ctx.author.mention} Успешно добавила, Нья! {emoji}')
        except Exception as e:
            await ctx.send(f'{ctx.author.mention} Не получилось добавить(\n{str(e)}')

    @create_new_emoji.error
    async def create_new_emoji_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'<@{ctx.author.id}> Ты не прикрепил картинку! Баака')

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'<@{ctx.author.id}> Ты не написал название эмодзи! Баака')



        #if isinstance(error, commands.CheckFailure):
            #await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}> и подключись к войсу <#{voice}>')





def setup(bot):
    bot.add_cog(Technical(bot))
